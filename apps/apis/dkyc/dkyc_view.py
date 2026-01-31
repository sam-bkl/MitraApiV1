from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.utils import timezone
from datetime import datetime
import base64, os
from .dkyc_models import CosBcdDkyc,DkycCustSignOtp, DkycPosSignOtp
from ..models import  Simprepaid, Simpostpaid
from .dekyc_serializers import CosBcdDkycCreateSerializer
from ..utils import is_sim_allotted_today, insert_sim_allotment
from ..helperviews.simswap import simswap_save
from .. import create_cafid
from ..inventory_movement.inv_update import update_inventory_atomic
from django.db import DatabaseError
from django.core.exceptions import ValidationError
import random
import os
import json
from django.conf import settings
from datetime import datetime
from ..send_sms import dkyc_send_sms
from django.db.models import Q
from apps.apis.dkyc.dkyc_models import BulkBusinessGroups,CompanyInformations,BulkConnectionDetails
from apps.apis.dkyc.dekyc_serializers import BulkBusinessSearchInputSerializer,BulkBusinessSearchOutputSerializer,BusinessGroupDetailInputSerializer,BusinessGroupDetailSerializer
import requests
import urllib3
from ..esim.esim_post_view import reserve_esim
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def dump_request_to_text(request, tag="dkyc"):
    try:
        base_dir = "/home/bsnlcos/dkyclog/"
        os.makedirs(base_dir, exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{tag}_{ts}.txt"
        filepath = os.path.join(base_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("=== DKYC REQUEST DUMP ===\n")
            f.write(f"Time: {datetime.now().isoformat()}\n")
            f.write(f"IP: {request.META.get('REMOTE_ADDR')}\n")
            f.write(f"Path: {request.path}\n")
            f.write(f"Method: {request.method}\n\n")

            f.write("---- HEADERS ----\n")
            for k, v in request.headers.items():
                f.write(f"{k}: {v}\n")

            f.write("\n---- RAW BODY ----\n")
            try:
                f.write(request.body.decode("utf-8", errors="ignore"))
            except Exception:
                f.write("<<Unable to decode body>>")

            f.write("\n\n---- PARSED DATA ----\n")
            f.write(json.dumps(request.data, indent=2, default=str))

        # restrict permissions
        os.chmod(filepath, 0o600)

    except Exception as e:
        # Never fail API due to logging
        pass


def get_client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    xri = request.META.get("HTTP_X_REAL_IP")
    ra = request.META.get("REMOTE_ADDR")

    if xff:
        return xff.split(",")[0].strip()
    if xri:
        return xri
    return ra

def save_base64_image(base64_data, caf_no, suffix):
    if not base64_data:
        return None

    try:
        decoded = base64.b64decode(base64_data)
    except Exception:
        raise ValueError("Invalid base64 image")

    today = timezone.localdate()
    base_dir = "/cosdata/files/cos_images/dkyc"
    path = os.path.join(
        base_dir,
        today.strftime("%Y"),
        today.strftime("%m"),
        today.strftime("%d")
    )

    os.makedirs(path, exist_ok=True)

    filename = f"{caf_no}{suffix}.jpg"
    full_path = os.path.join(path, filename)

    with open(full_path, "wb") as f:
        f.write(decoded)

    return full_path

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_dkyc_record(request):
    """
    Create DKYC record
    - Generates CAF ID
    - Saves images
    - Handles simswap
    - Inserts sim allotment
    """
    #dump_request_to_text(request, tag="create_dkyc")
    actual_ip = get_client_ip(request)

    # customer_aadhaar = request.data.get("customer_aadhaar")
    circle_code = request.data.get("circle_code")

    # if not customer_aadhaar:
    #     return Response(
    #         {"status": "error", "message": "customer_aadhaar is required"},
    #         status=status.HTTP_400_BAD_REQUEST
    #     )

    # ---- Aadhaar restriction check
    # exists, previous_gsm = is_sim_allotted_today(customer_aadhaar, circle_code)
    # if exists:
    #     return Response({
    #         "status": "failed",
    #         "message": "SIM already allotted today",
    #         "previous_gsm": previous_gsm
    #     }, status=status.HTTP_400_BAD_REQUEST)

    # ---- Generate CAF
    caf_type = request.data.get("dkyc_caf_type")
    if caf_type in ("cugsimswap", "cugmnp", "cugm2m","cug"):
        caf_no = create_cafid.get_caf_id("BDG")
    else:
        caf_no = create_cafid.get_caf_id("D")
    if not caf_no:
        return Response(
            {"status": "error", "message": "CAF generation failed"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # ---- Handle simswap before save
    
    mobileno = request.data.get("dkyc_selected_mobile_number")
    ctopupno = request.data.get("dkyc_parent_ctopup_number")
    circle_code = request.data.get("dkyc_circle_code")

    if caf_type == "simswap":
        result = simswap_save(request, caf_no, ctopupno, actual_ip, mobileno)
        if result.get("status") != "success":
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

    # ---- Prepare serializer data
    data = request.data.copy()
    data["caf_serial_no"] = caf_no
    data["device_ip"] = actual_ip

    serializer = CosBcdDkycCreateSerializer(data=data)

    if not serializer.is_valid():

    # 🔴 LOG VALIDATION ERROR HERE
        with open("/home/bsnlcos/apis/logs/dkyc_serializer_errors.txt", "a") as f:
            f.write(
                f"\n[{timezone.now()}] UpdateCAFDetailsSerializer ERROR\n"
                f"errors: {serializer.errors}\n"
                f"payload: {request.data}\n"
            )

        return Response(
            {
                "status": "error",
                "message": "Validation failed",
                "errors": serializer.errors
            },
            status=400
        )

    # if not serializer.is_valid():
    #     return Response({
    #         "status": "error",
    #         "message": "Validation failed",
    #         "errors": serializer.errors
    #     }, status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic(using="legacy"):
            sim_category = serializer.validated_data.get("dkyc_sim_category")

            record = serializer.save()

            # ⚠️ CRITICAL: Update inventory FIRST (before images)
            # If this fails, nothing gets saved
            connection_type = record.connection_type
            if sim_category =="esim":
                esim_obj = reserve_esim(circle_code,connection_type)
                simno = esim_obj.simno
                record.sim_no = simno
                record.sim_type = 3
            else:
                simno = record.sim_no
            
                # Set sim_type before inventory update
                if connection_type == 2:
                    sim = Simpostpaid.objects.filter(simno=simno).only("product_code").first()   
                else:
                    sim = Simprepaid.objects.filter(simno=simno).only("product_code").first() 
                
                if sim and sim.product_code in (7003, 7004):
                    record.sim_type = 2
                else:
                    record.sim_type = 1
            
            # Update inventory (will raise ValidationError if fails)
            if caf_type != "cugm2m":
                update_inventory_atomic(
                    simno=simno,
                    gsmno=record.gsmnumber,
                    connection_type=connection_type,
                    caf_type=caf_type,sim_mode=sim_category
                )
            
            # ---- Save images AFTER inventory succeeds
            record.poi_document_front = save_base64_image(
                request.data.get("dkyc_poiDocumentFront"), caf_no, "pif"
            )
            record.poi_document_back = save_base64_image(
                request.data.get("dkyc_poiDocumentBack"), caf_no, "pib"
            )
            record.poa_document_front = save_base64_image(
                request.data.get("dkyc_poaDocumentFront"), caf_no, "paf"
            )
            record.poa_document_back = save_base64_image(
                request.data.get("dkyc_poaDocumentBack"), caf_no, "pab"
            )
            record.customer_photo = save_base64_image(
                request.data.get("dkyc_customerPhoto"), caf_no, "l"
            )
            record.pos_photo = save_base64_image(
                request.data.get("dkyc_posPhoto"), caf_no, "p"
            )
            record.pwd_doc_photo = save_base64_image(
                request.data.get("dkyc_pwd_doc_photo"), caf_no, "pwd"
            )

            update_fields = [
                "sim_type",
                "poi_document_front",
                "poi_document_back",
                "poa_document_front",
                "poa_document_back",
                "customer_photo",
                "pos_photo",
                "pwd_doc_photo",
            ]

            if sim_category == "esim":
                update_fields.append("sim_no")

            record.save(update_fields=update_fields)
            # record.save(update_fields=[
            #                 "sim_type",
            #                 "poi_document_front",
            #                 "poi_document_back",
            #                 "poa_document_front",
            #                 "poa_document_back",
            #                 "customer_photo",
            #                 "pos_photo",
            #                 "pwd_doc_photo"
            #             ])
                        

            if caf_type in ( "cugmnp", "cugm2m","cug"):
                BulkConnectionDetails.objects.filter(
                    gsm_number=mobileno
                ).update(
                    act_status='P',
                    updated_at=timezone.now()
                )


            # Verification check
            if not CosBcdDkyc.objects.filter(caf_serial_no=caf_no).exists():
                raise DatabaseError("CAF insert failed")
                
            return Response({
                "status": "success",
                "message": "DKYC created successfully",
                "caf_id": caf_no,
                "mobileno": mobileno,
                "simnumber": simno,
                "category": connection_type,
                "time_act": timezone.now().isoformat()
            }, status=status.HTTP_201_CREATED)

    except ValidationError as e:
        return Response(
            {"status": "error", "message": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except DatabaseError as e:
        return Response(
            {"status": "error", "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
###########################################################################################################
######################### SMS VIEWS #######################################################################

OTP_TYPE_MAP = {
    "cust": {
        "model": DkycCustSignOtp,
        "field": "cust_no",
        "label": "Customer number",
        "sms_type": "Customer Signature"
    },
    "pos": {
        "model": DkycPosSignOtp,
        "field": "pos_no",
        "label": "POS number",
        "sms_type": "POS Signature"
    }
}
    
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def dkyc_send_otp(request):
    otp_type = request.data.get("otp_type", "").strip()
    number = request.data.get("number", "").strip()

    if otp_type not in OTP_TYPE_MAP:
        return Response(
            {"status": "error", "message": "Invalid otp_type"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not number:
        return Response(
            {
                "status": "error",
                "message": f"{OTP_TYPE_MAP[otp_type]['label']} required"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    config = OTP_TYPE_MAP[otp_type]
    model = config["model"]
    field = config["field"]
    sms_type = config["sms_type"]

    otp = str(random.randint(100000, 999999))

    model.objects.create(
        **{field: number, "otp": otp}
    )

    dkyc_send_sms(number, sms_type, otp)

    return Response(
        {
            "status": "success",
            "message": "OTP sent successfully",
            "otp_type": otp_type
        },
        status=status.HTTP_200_OK
    )

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def dkyc_verify_otp(request):
    otp_type = request.data.get("otp_type", "").strip()
    number = request.data.get("number", "").strip()
    otp = request.data.get("otp", "").strip()

    if otp_type not in OTP_TYPE_MAP:
        return Response(
            {"status": "error", "message": "Invalid otp_type"},
            status=status.HTTP_200_OK
        )

    if not number or not otp:
        return Response(
            {"status": "failure", "message": "Number and OTP are required"},
            status=status.HTTP_200_OK
        )

    config = OTP_TYPE_MAP[otp_type]
    model = config["model"]
    field = config["field"]

    record = model.objects.filter(
        **{field: number, "otp": otp}
    ).order_by("-created_at").first()

    if not record:
        return Response(
            {"status": "failure", "message": "Invalid OTP"},
            status=status.HTTP_200_OK
        )

    # 10 min expiry
    if (timezone.now() - record.created_at).total_seconds() > 600:
        record.delete()
        return Response(
            {"status": "failure", "message": "OTP expired"},
            status=status.HTTP_200_OK
        )

    # IMPORTANT for DKYC: delete after success
    record.delete()

    return Response(
        {
            "status": "success",
            "message": "OTP verified successfully",
            "otp_type": otp_type
        },
        status=status.HTTP_200_OK
    )

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def dkyc_resend_otp(request):
    otp_type = request.data.get("otp_type", "").strip()
    number = request.data.get("number", "").strip()

    if otp_type not in OTP_TYPE_MAP:
        return Response(
            {"status": "error", "message": "Invalid otp_type"},
            status=status.HTTP_200_OK
        )

    if not number:
        return Response(
            {"status": "error", "message": "Number required"},
            status=status.HTTP_200_OK
        )

    config = OTP_TYPE_MAP[otp_type]
    model = config["model"]
    field = config["field"]
    sms_type = config["sms_type"]

    last = model.objects.filter(
        **{field: number}
    ).order_by("-created_at").first()

    if last:
        elapsed = (timezone.now() - last.created_at).total_seconds()
        if elapsed < 30:
            return Response(
                {
                    "status": "error",
                    "message": "Please wait before resending OTP",
                    "wait_seconds": 30 - int(elapsed)
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

    otp = str(random.randint(100000, 999999))

    model.objects.create(
        **{field: number, "otp": otp}
    )

    dkyc_send_sms(number, sms_type, otp)

    return Response(
        {
            "status": "success",
            "message": "OTP resent successfully",
            "otp_type": otp_type
        },
        status=status.HTTP_200_OK
    )


################################################################################################################
##########################################CUG Search ###########################################################

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def search_bulk_business_groups(request):
    """
    Secure search API for bulk business groups
    
    """

    # -----------------------------
    # 1. Validate input
    # -----------------------------
    serializer = BulkBusinessSearchInputSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    # ✅ THESE LINES YOU ASKED ABOUT
    search_text = serializer.validated_data["search_text"]
    circle_code = serializer.validated_data.get("circle_code")
    connectionCategory = serializer.validated_data["connectionCategory"]
    cafType = serializer.validated_data.get("cafType")

    if cafType and cafType.lower() == "m2m":
        try:
            # Get proxy settings - use None to bypass proxy
            use_proxy = getattr(settings, "USE_M2M_PROXY", False)
            proxies = getattr(settings, "PROXIES", None) if use_proxy else None
            
            response = requests.post(
                "https://m2mbsnlkerala.bsnl.co.in/api/SearchCustomerDetails",
                params={"customer_name": search_text},
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                proxies=proxies,  # None means no proxy
                timeout=(10, 30),  # Increased timeout (connect, read)
                verify=False  # Disable SSL verification
            )
            response.raise_for_status()
            external_data = response.json()

        except requests.exceptions.Timeout:
            return Response(
                {
                    "status": "error",
                    "message": "M2M API request timed out",
                },
                status=status.HTTP_504_GATEWAY_TIMEOUT
            )

        except requests.exceptions.SSLError as e:
            return Response(
                {
                    "status": "error",
                    "message": "SSL error connecting to M2M API",
                },
                status=status.HTTP_502_BAD_GATEWAY
            )

        except requests.exceptions.HTTPError as e:
            return Response(
                {
                    "status": "error",
                    "message": f"M2M API returned error: {e.response.status_code}",
                },
                status=status.HTTP_502_BAD_GATEWAY
            )

        except requests.RequestException as e:
            return Response(
                {
                    "status": "error",
                    "message": "Failed to fetch M2M customer data",
                },
                status=status.HTTP_502_BAD_GATEWAY
            )

        # Normalize external response to your API format
        results = [
            {
                "business_group_id": item.get("cug_id"),
                "reference_number": item.get("customer_id"),
                "company_name": item.get("company_name"),
                "registered_address1": "",
                "registered_district": "",
            }
            for item in external_data
        ]

        output_serializer = BulkBusinessSearchOutputSerializer(results, many=True)

        return Response(
            {
                "status": "success",
                "count": len(output_serializer.data),
                "data": output_serializer.data,
            },
            status=status.HTTP_200_OK
        )


    # -----------------------------
    # 2. ORM query (SAFE)
    # -----------------------------
    queryset = (
    BulkBusinessGroups.objects
    .filter(
        status="Approved",
        circle_code = circle_code
    )
    .filter(
        Q(reference_number__icontains= search_text ) |
        Q(companyinformations__company_name__icontains= search_text)
    )
    .values(
        "business_group_id",
        "reference_number",
        "companyinformations__company_name",
        "companyinformations__registered_address1",
        "companyinformations__registered_district",
    )
    .distinct()
    )

    # -----------------------------
    # 3. Normalize keys for output
    # -----------------------------
    results = [
    {
        "business_group_id": row["business_group_id"],
        "reference_number": row["reference_number"],
        "company_name": row["companyinformations__company_name"],
        "registered_address1": row["companyinformations__registered_address1"],
        "registered_district": row["companyinformations__registered_district"],
    }
    for row in queryset
    ]

    output_serializer = BulkBusinessSearchOutputSerializer(results, many=True)

    return Response(
        {
            "status": "success",
            "count": len(output_serializer.data),
            "data": output_serializer.data
        },
        status=200
    )

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def get_business_group_details(request):
    """
    Returns:
    - Business group details
    - Company information
    - First 20 GSM + SIM numbers
    """

    # ---------------------------
    # 1. Validate input
    # ---------------------------
    serializer = BusinessGroupDetailInputSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    business_group_id = serializer.validated_data["business_group_id"]
    connectionCategory = serializer.validated_data["connectionCategory"]
    cafType = serializer.validated_data.get("cafType")

    if cafType and cafType.lower() == "m2m":
        try:
            # Get proxy settings
            proxies = getattr(settings, "PROXIES", None)
            verify_ssl = getattr(settings, "M2M_VERIFY_SSL", False)
            
            response = requests.post(  # Keep POST as in Postman
                "https://m2mbsnlkerala.bsnl.co.in/api/GetNewCustomerDetails",
                params={"customer_id": business_group_id},
                headers={
                    "Accept": "application/json",
                    # Remove Content-Type for params-only POST
                },
                proxies=proxies,
                timeout=(3, 5),
                verify=verify_ssl
            )
            response.raise_for_status()
            m2m_data = response.json()
            
            # Map M2M response to your structure
            company = {
                "company_name": m2m_data.get("company_name"),
                "registered_address1": m2m_data.get("registered_address1"),
                "registered_address2": m2m_data.get("registered_address2"),
                "registered_district": m2m_data.get("registered_district"),
                "registered_state": m2m_data.get("registered_state"),
                "registered_pin_code": m2m_data.get("registered_pincode"),
            }
            
            # Map connection details from M2M data
            connections = [{
                "gsm_number": m2m_data.get("msisdn"),
                "sim_number": m2m_data.get("sim_no"),
                "customer_name": m2m_data.get("auth_first_name"),
                "user_name": None,  # Not in M2M response
                "poi_type": m2m_data.get("poi_type"),
                "poi_number": m2m_data.get("poi_number"),
                "poa_type": m2m_data.get("poa_type"),
                "poa_number": m2m_data.get("poa_number"),
                "designation": None,  # Not in M2M response
                "alternate_no": m2m_data.get("contact_number"),
            }]
            
            # Build response from M2M data
            response_data = {
                "business_group_id": m2m_data.get("customer_id"),
                "reference_number": m2m_data.get("customer_id"), 
                "business_group_name": m2m_data.get("business_group_name"),
                "business_group_type": m2m_data.get("business_group_type"),
                "connection_type": m2m_data.get("connection_type"),
                "business_group_size": m2m_data.get("business_group_size"),
                "status": "active",  # Assuming active if data exists
                "company": company,
                "connections": connections,
            }
            
            output = BusinessGroupDetailSerializer(response_data)
            
            return Response(
                {
                    "status": "success",
                    "data": output.data,
                    "source": "m2m_api"
                },
                status=200
            )

        except requests.exceptions.Timeout:
            return Response(
                {
                    "status": "error",
                    "message": "M2M API request timed out"
                },
                status=status.HTTP_504_GATEWAY_TIMEOUT
            )

        except requests.exceptions.HTTPError as e:
            return Response(
                {
                    "status": "error",
                    "message": f"M2M API error: {e.response.status_code}"
                },
                status=status.HTTP_502_BAD_GATEWAY
            )

        except requests.RequestException:
            return Response(
                {
                    "status": "error",
                    "message": "Failed to fetch M2M customer details"
                },
                status=status.HTTP_502_BAD_GATEWAY
            )

    # ---------------------------
    # 2. Fetch business group
    # ---------------------------
    try:
        bbg = BulkBusinessGroups.objects.get(
            business_group_id=business_group_id
        )
    except BulkBusinessGroups.DoesNotExist:
        return Response(
            {
                "status": "failure",
                "message": "Business group not found"
            },
            status=404
        )

    # ---------------------------
    # 3. Fetch company info
    # ---------------------------
    company = (
        CompanyInformations.objects
        .filter(business_group_id=business_group_id)
        .values(
            "company_name",
            "registered_address1",
            "registered_address2",
            "registered_district",
            "registered_state",
            "registered_pin_code",
            "govt_flag"
        )
        .first()
    )
    if company["govt_flag"] == "Y":
        dkyc_done = BulkConnectionDetails.objects.filter(
            business_group_id=business_group_id,
            act_status="P"
        ).exists()

        if dkyc_done:
            return Response(
                {
                    "status": "failure",
                    "message": "DKYC already done for master number"
                },
                status=200
            )
        else:
            connections = (
            BulkConnectionDetails.objects
            .filter(business_group_id=business_group_id)
            .exclude(act_status="P")
            .order_by("serial_no")
            .values("gsm_number", "sim_number","customer_name","user_name","poi_type","poi_number","poa_type","poa_number","designation","alternate_no")[:1]
        )
    # ---------------------------
    # 4. Fetch first 20 connections
    # ---------------------------
    connections = (
        BulkConnectionDetails.objects
        .filter(business_group_id=business_group_id)
        .exclude(act_status="P")
        .order_by("serial_no")
        .values("gsm_number", "sim_number","customer_name","user_name","poi_type","poi_number","poa_type","poa_number","designation","alternate_no")[:20]
    )
   
    # ---------------------------
    # 5. Build response payload
    # ---------------------------
    response_data = {
        "business_group_id": bbg.business_group_id,
        "reference_number": bbg.reference_number,
        "business_group_name": bbg.business_group_name,
        "business_group_type": bbg.business_group_type,
        "connection_type": bbg.connection_type,
        "business_group_size": bbg.business_group_size,
        "status": bbg.status,
        "company": company,
        "connections": list(connections),
    }

    output = BusinessGroupDetailSerializer(response_data)

    return Response(
        {
            "status": "success",
            "data": output.data
        },
        status=200
    )