from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from apps.apis.inventory_movement.inv_update import update_inventory_atomic
from .serializers import SimUpgradeRequestSerializer, AppUpgradeOptionsSerializer, SimUpgradeRequestListSerializer
from apps.apis.utils import get_client_ip
from django.utils.timezone import now
from django.db.models import Q
from .models import AppUpgradeOptions, SimUpgradeRequest
from apps.apis.models import Simpostpaid, Simprepaid, SimpostpaidSold, SimprepaidSold
from .status_upd_upg import fetch_sim_swap_status
from apps.apis.external_data.pyro_usim.pyro_api import get_pyro_usim_imsi

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_sim_upgrade_request(request):
    data = request.data

    # =========================
    # 1. Validate SS payload
    # =========================
    ss_list = data.get("simUpgradeDetailsFromSS", [])
    if not ss_list or not isinstance(ss_list, list):
        return Response(
            {"message": "simUpgradeDetailsFromSS is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    ss = ss_list[0]  # agreed: single SS object
    conn_type_str = (data.get("connectionType") or "").lower()
    simno= data.get("simNumber")
    gsmno = data.get("mobileNumber")
    circle_code = data.get("cst_cir_code")
    activation_type='4GUPGRADE'
    if SimUpgradeRequest.objects.filter(mobile_number=gsmno).exists():
        return Response(
            {
                "status": "failure",
                "message": "SIM upgrade request already exists for this mobile number"
            },
            status=409   # Conflict is correct HTTP code
        )

    if conn_type_str == "prepaid":
        connection_type = 1
        imsi, product_code = (
        Simprepaid.objects
        .filter(simno=simno)
        .values_list("imsi", "product_code")
        .first() or (None, None)
    )
        imsi_old = (
        SimprepaidSold.objects
        .filter(simno=simno)
        .values_list("imsi", flat=True)
        .first()
        )
    elif conn_type_str == "postpaid":
        connection_type = 2
        imsi, product_code = (
            Simpostpaid.objects
            .filter(simno=simno)
            .values_list("imsi", "product_code")
            .first() or (None, None)
        )
        imsi_old =(
        SimpostpaidSold.objects
        .filter(simno=simno)
        .values_list("imsi", flat=True)
        .first()
        )
    else:
        return Response(
            {"message": "Invalid connectionType. Use prepaid or postpaid"},
            status=status.HTTP_400_BAD_REQUEST
        )
    if product_code in (7003, 7004):
        sim_type = 2
        result = get_pyro_usim_imsi(gsmno,simno,circle_code,connection_type)
        activation_type='4GUPGRADE-USIM'
        if not result["success"]:
            return Response(
                {
                    "status": "success",
                    "message": "USIM IMSI Fetch failed"
                },
                status=status.HTTP_200_OK
            )
        else:
            imsi= result["imsi"]
    else:
        sim_type = 1 
    # =========================
    # 2. Flatten payload
    # =========================
    payload = {
        # ----- Request level -----
        "process_type": data.get("processType"),
        "connection_type": connection_type,
        "exchange_reason": data.get("exchangeReason"),
        "exchange_reason_id": data.get("exchangeReasonId"),
        "mobile_number": data.get("mobileNumber"),
        "imsi": imsi,
        "imsi_old":imsi_old,
        "sim_type" :sim_type,
        "is_otp_verified": data.get("isOtpVerified"),
        "otp_received": data.get("otpReceived"),
        "verified_at": data.get("verifiedAt"),
            
        "sim_number": data.get("simNumber"),
        "parent_ctop_number" : data.get("parent_ctop_number"),
        "csc_code" : data.get("vendor_code"),
        "alternate_mobile_number":data.get("alternate_mobile_number"),
        "cust_circle_code":data.get("cst_cir_code"),
        "pos_circle_code": data.get("pos_circle_code"),
        "mpin": data.get("mpin"),

        # ----- SS Details -----
        "account_no": ss.get("ACCOUNT_NO"),

        "bill_fname": ss.get("BILL_FNAME"),
        "bill_lname": ss.get("BILL_LNAME"),
        "bill_minit": ss.get("BILL_MINIT"),

        "bill_address1": ss.get("BILL_ADDRESS1"),
        "bill_address2": ss.get("BILL_ADDRESS2"),
        "bill_address3": ss.get("BILL_ADDRESS3"),

        "bill_city": ss.get("BILL_CITY"),
        "bill_state": ss.get("BILL_STATE"),
        "bill_zip": ss.get("BILL_ZIP"),

        "in_active_date": ss.get("IN_ACTIVE_DATE"),
        "emf_config_id": ss.get("EMF_CONFIG_ID"),

        "ss_connection_type": ss.get("CONNECTION_TYPE"),
        "uid_no": ss.get("UID_NO"),
        "customer_uid_token": ss.get("CUSTOMER_UID_TOKEN"),

        "act_type": ss.get("ACT_TYPE"),
        "acc_balance": ss.get("ACC_BALANCE"),

        "ss_simnumber": ss.get("SIMNUMBER"),
        "amount_req": ss.get("AMOUNT_REQ"),

        "caf_serial_no": ss.get("CAF_SERIAL_NO"),
        "ssa_code": ss.get("SSA_CODE"),
        "remarks": ss.get("REMARKS"),

        # ----- Audit -----
        "insert_user": request.user.username,
        "ins_user_ip": get_client_ip(request),
        "activation_type":activation_type
        
    }
    simno= data.get("simNumber")
    gsmno = data.get("mobileNumber")
    # =========================
    # 3. Atomic insert
    # =========================
    #try:
    with transaction.atomic(using='legacy'):
        serializer = SimUpgradeRequestSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        plan="simupgrade"
        update_inventory_atomic(simno, gsmno, connection_type, plan)
            # 🔐 Future-proof hook
            # place any critical DB updates here
            # e.g. inventory update, SIM status update

    # except Exception as e:
    #     return Response(
    #         {
    #             "status": "failure",
    #             "message": "Failed to create SIM upgrade request",
    #             "error": str(e)
    #         },
    #         status=status.HTTP_400_BAD_REQUEST
    #     )

    return Response(
        {
            "status": "success",
            "id": obj.id,
            "message": "SIM upgrade request created successfully"
        },
        status=status.HTTP_200_OK
    )

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def get_app_upgrade_options(request):
    """
    POST body:
    {
        "circle_code": "50"
    }
    """

    circle_code = request.data.get("circle_code")

    if not circle_code:
        return Response(
            {
                "status": "failure",
                "message": "circle_code is required"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    today = now().date()

    qs = AppUpgradeOptions.objects.filter(
        Q(circle_code=circle_code) | Q(circle_code="9999"),
        start_date__lte=today
    ).filter(
        Q(end_date__gte=today) | Q(end_date__isnull=True)
    )

    # -------------------------
    # Prefer circle-specific rows
    # -------------------------
    seen_values = set()
    final_rows = []

    for row in qs.order_by("-circle_code", "id"):
        if row.value not in seen_values:
            seen_values.add(row.value)
            final_rows.append(row)

    serializer = AppUpgradeOptionsSerializer(final_rows, many=True)

    return Response(
        {
            "status": "success",
            "count": len(final_rows),
            "data": serializer.data
        },
        status=status.HTTP_200_OK
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def list_sim_upgrade_requests(request):
    """
    POST body:
    {
        "username": "POS123"
    }
    """

    username = request.data.get("username")

    if not username:
        return Response(
            {
                "status": "failure",
                "message": "username is required"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    qs = SimUpgradeRequest.objects.filter(
        insert_user=username
    ).order_by("-created_at")

    mobile_numbers = list(
        qs.values_list("mobile_number", flat=True)
    )

    # 🔥 Single Oracle hit
    oracle_status_map = fetch_sim_swap_status(mobile_numbers)

    serializer = SimUpgradeRequestListSerializer(
        qs,
        many=True,
        context={"oracle_status_map": oracle_status_map}
    )

    return Response(
        {
            "status": "success",
            "count": qs.count(),
            "data": serializer.data
        },
        status=status.HTTP_200_OK
    )