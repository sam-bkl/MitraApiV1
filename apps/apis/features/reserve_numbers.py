from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction, DatabaseError
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from ..models import GsmChoice
from .feature_config import RESERVATION_RULES
from django.utils import timezone

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reserve_gsm_number(request):
    """
    Reserve a GSM number

    Request JSON:
    {
        "gsmno": "9494542730",
        "mpin": "9876543210",
        "username": "POS123",
        "parent_ctop_number": "CTOP456",
        "circle_code": 50
    }
    """

    gsmno = request.data.get("gsmno")
    mpin = request.data.get("mpin")
    username = request.data.get("username")
    parent_ctop = request.data.get("parent_ctop_number")
    circle_code = request.data.get("circle_code")

    if not all([gsmno, mpin, username, parent_ctop, circle_code]):
        return Response(
            {"status": "failure", "message": "Missing required fields"},
            status=status.HTTP_400_BAD_REQUEST
        )

    now = timezone.now()
    max_days = RESERVATION_RULES["max_days"]
    max_numbers = RESERVATION_RULES["max_numbers"]

    try:
        with transaction.atomic(using="legacy"):

            # 🔒 Count active reservations by this user
            active_count = (
                GsmChoice.objects
                .using("legacy")
                .filter(
                    reserve_username=username,
                    reserve_end_date__gte=now
                )
                .count()
            )

            if active_count >= max_numbers:
                raise DatabaseError(
                    f"Reservation limit exceeded ({max_numbers} numbers allowed)"
                )

            # 🔒 Lock GSM row
            gsm = (
                GsmChoice.objects
                .using("legacy")
                .select_for_update()
                .filter(
                    gsmno=gsmno,
                    circle_code=circle_code
                )
                .first()
            )

            if not gsm:
                raise DatabaseError("GSM number not found")

            # ❌ Already reserved and not expired
            if gsm.reserve_end_date and gsm.reserve_end_date >= now:
                raise DatabaseError(
                    f"GSM already reserved until {gsm.reserve_end_date}"
                )

            # ✅ Reserve GSM
            gsm.reserve_start_date = now
            gsm.reserve_end_date = now + timedelta(days=max_days)
            gsm.reserve_username = username
            gsm.reserve_ctopnumber = parent_ctop

            gsm.save(update_fields=[
                "reserve_start_date",
                "reserve_end_date",
                "reserve_username",
                "reserve_ctopnumber"
            ])

            return Response(
                {
                    "status": "success",
                    "message": "GSM reserved successfully",
                    "gsmno": gsm.gsmno,
                    "reserved_until": gsm.reserve_end_date,
                    "allowed_days": max_days,
                    "user_limit": max_numbers
                },
                status=status.HTTP_200_OK
            )

    except DatabaseError as e:
        return Response(
            {"status": "failure", "message": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def get_reserved_gsm_numbers(request):
    """
    Return ONLY reserved GSM numbers
    """

    username = request.data.get("username")
    parent_ctop = request.data.get("parent_ctop_number")
    circle_code = request.data.get("circle_code")
    gsm_type = request.data.get("gsm_type")  # optional: cymn | fancy

    if not all([username, parent_ctop, circle_code]):
        return Response(
            {
                "status": "failure",
                "message": "username, parent_ctop_number and circle_code are required",
                "data": []
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        now_ts = timezone.now()

        qs = (
            GsmChoice.objects.using("read")
            .filter(
                reserve_username=username,
                reserve_ctopnumber=parent_ctop,
                circle_code=int(circle_code),
                reserve_end_date__gte=now_ts
            )
        )

        # -------------------------
        # GSM TYPE FILTER (OPTIONAL)
        # -------------------------
        reserved_numbers = list(
            qs.values_list("gsmno", flat=True).order_by("gsmno")
        )

        return Response(
            {
                "status": "success",
                "message": "Reserved numbers found" if reserved_numbers else "No reserved numbers",
                "count": len(reserved_numbers),
                "data": reserved_numbers
            },
            status=status.HTTP_200_OK
        )

    except Exception as e:
        return Response(
            {
                "status": "failure",
                "message": f"Error: {str(e)}",
                "data": []
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
