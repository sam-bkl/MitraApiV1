from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Esimprepaid, EmailOtpTable
from .serializers import EsimprepaidSerializer
from django.utils import timezone
import random
from datetime import timedelta
from django.core.mail import EmailMessage
from django.conf import settings


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def get_esim_by_simnumber(request):
    """
    POST body:
    {
        "simnumber": "8991555074590274058"
    }
    """

    simnumber = request.data.get("simnumber")

    if not simnumber:
        return Response(
            {
                "status": "failure",
                "message": "simnumber is required"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    records = Esimprepaid.objects.filter(simno=simnumber)

    if not records.exists():
        return Response(
            {
                "status": "failure",
                "message": "No eSIM record found",
                "simnumber": simnumber
            },
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = EsimprepaidSerializer(records, many=True)

    return Response(
        {
            "status": "success",
            "count": records.count(),
            "data": serializer.data
        },
        status=status.HTTP_200_OK
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def email_verify_otp(request):

    email = request.data.get("email_id", "").strip().lower()
    otp = request.data.get("otp", "").strip()

    if not email or not otp:
        return Response(
            {
                "status": "failure",
                "message": "Email ID and OTP are required"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    otp_record = (
        EmailOtpTable.objects
        .filter(email_id=email, otp=otp)
        .order_by("-created_at")
        .first()
    )

    if not otp_record:
        return Response(
            {
                "status": "failure",
                "message": "Invalid OTP"
            },
            status=status.HTTP_200_OK
        )

    # OTP expiry – 10 minutes
    otp_age = (timezone.now() - otp_record.created_at).total_seconds()
    if otp_age > 600:
        otp_record.delete()
        return Response(
            {
                "status": "failure",
                "message": "OTP expired. Please request a new one."
            },
            status=status.HTTP_200_OK
        )
    otp_record.delete()
    return Response(
        {
            "status": "success",
            "message": "OTP verified successfully",
            "email_id": email,
            "verified_at": otp_record.created_at
        },
        status=status.HTTP_200_OK
    )

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def email_resend_otp(request):

    email = request.data.get("email_id", "").strip().lower()
    purpose = request.data.get("purpose", "EMAIL_VERIFICATION")

    if not email:
        return Response(
            {
                "status": "failure",
                "message": "Email ID is required"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Cooldown check – 30 seconds
    last_otp = (
        EmailOtpTable.objects
        .filter(email_id=email)
        .order_by("-created_at")
        .first()
    )

    if last_otp:
        elapsed = timezone.now() - last_otp.created_at
        if elapsed < timedelta(seconds=30):
            return Response(
                {
                    "status": "failure",
                    "message": "Please wait before resending OTP",
                    "wait_seconds": 30 - int(elapsed.total_seconds())
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

    # Generate OTP
    otp = str(random.randint(100000, 999999))

    # Save OTP
    EmailOtpTable.objects.create(
    email_id=email,
    otp=otp,
    purpose=purpose,
    created_at=timezone.now()
    )

    # Send email
    email_msg = EmailMessage(
        subject="BSNL Email OTP Verification",
        body=f"Your OTP is {otp}. It is valid for 10 minutes.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email],
    )
    email_msg.send(fail_silently=False)

    return Response(
        {
            "status": "success",
            "message": "OTP sent successfully",
            "email_id": email
        },
        status=status.HTTP_200_OK
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_email_otp(request):
    """
    Send Email OTP (first time)
    """

    email = request.data.get("email_id", "").strip().lower()
    purpose =  "ESIM_EMAIL_VERIFICATION"

    if not email:
        return Response(
            {
                "status": "failure",
                "message": "Email ID is required"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # ---------------------------
    # Optional cooldown (30 sec)
    # ---------------------------
    last_otp = (
        EmailOtpTable.objects
        .filter(email_id=email, purpose=purpose)
        .order_by("-created_at")
        .first()
    )

    if last_otp:
        elapsed = timezone.now() - last_otp.created_at
        if elapsed < timedelta(seconds=30):
            return Response(
                {
                    "status": "failure",
                    "message": "Please wait before requesting OTP again",
                    "wait_seconds": 30 - int(elapsed.total_seconds())
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

    # ---------------------------
    # Generate OTP
    # ---------------------------
    otp = str(random.randint(100000, 999999))

    # ---------------------------
    # Save OTP
    # ---------------------------
    EmailOtpTable.objects.create(
    email_id=email,
    otp=otp,
    purpose=purpose,
    created_at=timezone.now()   # ✅ FIX
    )

    # ---------------------------
    # Send Email
    # ---------------------------
    email_msg = EmailMessage(
        subject="BSNL Email OTP Verification",
        body=f"Your OTP is {otp}. It is valid for 10 minutes.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email],
    )

    email_msg.send(fail_silently=False)

    return Response(
        {
            "status": "success",
            "message": "OTP sent successfully",
            "email_id": email
        },
        status=status.HTTP_200_OK
    )