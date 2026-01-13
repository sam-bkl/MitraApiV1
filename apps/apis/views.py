# views.py
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.permissions import IsAuthenticated , AllowAny
from .models import CtopMaster,Simprepaid, Simpostpaid, GsmChoice ,ApiOtpTable, AppVersion,RefOtpTable,CosBcd,FrcPlan,SimpostpaidSold,SimprepaidSold, PostpaidPlansApp,UpgradationOtpTable, SimAllotmentAdh
from .serializers import CtopMasterSerializer,SimprepaidSerializer,SimpostpaidSerializer,GsmChoiceSerializer,AppVersionSerializer
import random
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.cache import cache
from .send_sms import send_sms, ref_send_sms, upg_send_sms
from .resend_sms import resend_sms
from django.utils import timezone
from datetime import datetime, timedelta
import requests,json
import time
from django.utils.timezone import now
from django.db import transaction
from django.db.models import Q
from django.forms.models import model_to_dict
from .utils import is_sim_allotted_today
import logging
from .dkyc.dkyc_models import CosBcdDkyc
from itertools import chain

logger = logging.getLogger(__name__)

@api_view(['POST'])
def check_ctopupno(request):
    """
    Check if a CTOP UP number exists in the database
    
    Expected POST data:
    {
        "ctopupno": "12345678901234"
    }
    """
    t0 = time.time()
    ctopupno = request.data.get('ctopupno', '').strip()
    
    # Validate input
    if not ctopupno:
        return Response(
            {
                'status': "failure",
                'message': 'CTOP UP number is required',
                'data': None
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    t1 = time.time()
    try:
        # Check if the CTOP UP number exists
        #ctop = CtopMaster.objects.get(username=ctopupno)
        ctop = CtopMaster.objects.get(
                username=ctopupno,
                end_date__isnull=True
            )
        if ctop.circle_code == "65":
            return Response(
            {
                
                'status': "failure",
                'message': 'Not authorised',
                #'data': serializer.data
            },
            status=status.HTTP_401_UNAUTHORIZED
        )
        # if ctop.zone_code == "NZ" or ctop.zone_code == "EZ" :
        #     return Response(
        #     {
                
        #         'status': "failure",
        #         'message': 'Not authorised',
        #         #'data': serializer.data
        #     },
        #     status=status.HTTP_401_UNAUTHORIZED
        # )
        t2 = time.time()
        # If found, return success with data
        serializer = CtopMasterSerializer(ctop)
        t3 = time.time()
        otp = str(random.randint(100000, 999999))
        
        # Save OTP in database
        ApiOtpTable.objects.create(
            ctopupno=ctop.username,
            otp=otp
        )
        t4 = time.time()
        send_sms(ctop.username,otp)
        t5 = time.time()
        total = t5 - t0
        # print(f"""
        #     --- Timing Breakdown ---
        #     Input validation: {t1 - t0:.4f}s
        #     ORM fetch:        {t2 - t1:.4f}s
        #     Serialization:    {t3 - t2:.4f}s
        #     OTP Insert:       {t4 - t3:.4f}s
        #     SMS Send:         {t5 - t4:.4f}s
        #     TOTAL:            {total:.4f}s
        #     """)
        return Response(
            {
                
                'status': "success",
                'message': 'CTOP UP number found',
                #'data': serializer.data
            },
            status=status.HTTP_200_OK
        )
    
    except CtopMaster.DoesNotExist:
        # If not found, return failure
        return Response(
            {
                
                'status': "failure",
                'message': 'CTOP UP number does not exist',
                #'data': None
            },
            status=status.HTTP_404_NOT_FOUND
        )
    
    except Exception as e:
        # Handle any other errors
        return Response(
            {
                'status': "failure",
                'message': f'Error: {str(e)}',
                'data': None
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
def check_otp(request):

    ctopupno = request.data.get('ctopupno', '').strip()
    otp = request.data.get('otp', '').strip()

    # Validate required fields
    if not ctopupno or not otp:
        return Response(
            {
                'status': "failure",
                'message': 'CTOP UP number and OTP are required',
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Check CTOP exists
        record = CtopMaster.objects.get(username=ctopupno)

        # Verify OTP
        otp_record = ApiOtpTable.objects.filter(
            ctopupno=record.username,
            otp=otp
        ).order_by('-created_at').first()

        otp_age = (timezone.now() - otp_record.created_at).total_seconds()
        if otp_age > 600:  # 10 minutes
            # Delete expired OTP
            otp_record.delete()
            return Response(
                {
                    'status': "failure",
                    'message': 'OTP has expired. Please request a new one.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        ctop = CtopMaster.objects.get(username=ctopupno)

        brute_force_key = f"login_attempts_{ctopupno}"

        # Create refresh token
        refresh = RefreshToken()  # <-- IMPORTANT CHANGE

        refresh['exp'] = int((timezone.now() + timedelta(days=7)).timestamp())
        refresh['iat'] = int(timezone.now().timestamp())
        refresh['token_type'] = 'refresh'

        # Add custom claims
        refresh['ctopupno'] = ctop.username
        refresh['name'] = ctop.name

        # Access token from refresh
        access_token = refresh.access_token

        # Clear brute-force counter
        cache.delete(brute_force_key)
        if not ctop.aadhaar_no:
            aadhaar_no = "na"
        else:
            aadhaar_no = ctop.aadhaar_no
        
        if otp_record:
            # SUCCESS
            otp_record.delete()
            return Response(
                {
                    'status': "success",
                    'message': 'OTP verified successfully',
                    'access_token':str(access_token),
                    'refresh_token':str(refresh),
                    'data':{
                    #'ctopup_number':ctop.username,
                    'ctopup_number':ctop.ctopupno,
                    'username':ctop.username,
                    'ssa_code':ctop.ssa_code,
                    'simswap_allowed':ctop.swap_allowed,
                    'name': ctop.name,
                    'vendor_code':ctop.attached_to,
                    'circle_code':str(ctop.circle_code),
                    'aadhaar_no':aadhaar_no
                    }
                },
                status=status.HTTP_200_OK
            )

        # OTP not found or incorrect
        return Response(
            {
                'status': "failure",
                'message': 'Invalid OTP'
            },
            status=status.HTTP_200_OK
        )

    except CtopMaster.DoesNotExist:
        return Response(
            {
                'status': "failure",
                'message': 'CTOP UP number does not exist',
            },
            status=status.HTTP_200_OK
        )

    except Exception as e:
        return Response(
            {
                'status': "failure",
                'message': f'Error: {str(e)}'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_postpaid(request):
    """
    Expected POST:
    {   "sim_no": "12345678910",
        "last5": "12345",
        "vendor_code": "V001"
    }
    """
    sim_no= request.data.get('sim_no', '').strip()
    last5 = request.data.get('last5', '').strip()
    vendor_code = request.data.get('vendor_code', '').strip()
    
    # Validate last5
    if not last5 or len(last5) != 5 or not last5.isdigit():
        return Response(
            {
                'status': "failure",
                "message": "A valid 5-digit 'last5' value is required",
                "data": None
            },
            status=status.HTTP_200_OK
        )

    # Validate vendor_code
    if not vendor_code:
        return Response(
            {
                'status': "failure",
                "message": "'vendor_code' is required",
                "data": None
            },
            status=status.HTTP_200_OK
        )
    try:
        with transaction.atomic():
            sims = Simpostpaid.objects.using("read").filter(
                status=1,
                location=vendor_code,
                simno__endswith=last5
            )
            # sims = Simprepaid.objects.filter(
            #     status=1,
            #     location=vendor_code,
            #     simno__endswith=last5
            # )

            if not sims.exists():
                return Response(
                    {
                        "status": "failure",
                        "message": "No matching SIM found",
                        "data": []
                    },
                    status=status.HTTP_200_OK
                )

            serializer = SimpostpaidSerializer(sims, many=True)

            # Return only simno list (clean output)
            #simnos = [{"simno": item["simno"]} for item in serializer.data]

            if sim_no and sim_no.isdigit() and len(sim_no) == 19:
                simnos = [
                    {"simno": item["simno"]}
                    for item in serializer.data
                    if item["simno"] == sim_no
                ]
            else:
                simnos = [{"simno": item["simno"]} for item in serializer.data]

            return Response(
                {
                    "status": "success",
                    "message": f"{len(simnos)} SIM(s) found",
                    "data": simnos
                },
                status=status.HTTP_200_OK
            )

    except Exception as e:
        return Response(
            {
                "status": "failure",
                "message": "Internal server error",
                "error": str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # try:
    #     # Query logic:
    #     # sim = Simpostpaid.objects.get(
    #     #     status=1,
    #     #     location=vendor_code,
    #     #     simno__endswith=last5
    #     # )
    #     with transaction.atomic():
    #         sim = Simpostpaid.objects.get(
    #             status=1,
    #             location=vendor_code,
    #             simno__endswith=last5
    #         )
    #         # sim = (
    #         #     Simpostpaid.objects
    #         #     .filter(
    #         #         status=1,
    #         #         location=vendor_code,
    #         #         simno__endswith=last5
    #         #     )
    #         #     .exclude(product_code__in=['7004', '7003'])
    #         #     .first()
    #         # )

    #     serializer = SimpostpaidSerializer(sim)
    #     simno = {'simno': serializer.data["simno"]}

    #     return Response(
    #         {
                
    #             'status': "success",
    #             "message": "SIM found",
    #             "data": simno
    #         },
    #         status=status.HTTP_200_OK
    #     )

    # except Simpostpaid.DoesNotExist:
    #     return Response(
    #         {
    #             'status': "failure",
    #             "message": "No matching SIM found",
    #             "data": None
    #         },
    #         status=status.HTTP_200_OK
    #     )

    # except Exception as e:
    #     return Response(
    #         {
    #             'status': "failure",
    #             "message": f"Error: {str(e)}",
    #             "data": None
    #         },
    #         status=status.HTTP_500_INTERNAL_SERVER_ERROR
    #     )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_prepaid(request):
    """
    Expected POST:
    {
        "last5": "12345",
        "vendor_code": "V001"
    }
    """
    sim_no= request.data.get('sim_no', '').strip()
    last5 = request.data.get('last5', '').strip()
    vendor_code = request.data.get('vendor_code', '').strip()

    # Validate last5
    if not last5 or len(last5) != 5 or not last5.isdigit():
        return Response(
            {
                'status': "failure",
                "message": "A valid 5-digit 'last5' value is required",
                "data": None
            },
            status=status.HTTP_200_OK
        )

    # Validate vendor_code
    if not vendor_code:
        return Response(
            {
                'status': "failure",
                "message": "'vendor_code' is required",
                "data": None
            },
            status=status.HTTP_200_OK
        )
    try:
        with transaction.atomic():
            sims = Simprepaid.objects.using("read").filter(
                status=1,
                location=vendor_code,
                simno__endswith=last5
            )
            # sims = Simprepaid.objects.filter(
            #     status=1,
            #     location=vendor_code,
            #     simno__endswith=last5
            # )

            if not sims.exists():
                return Response(
                    {
                        "status": "failure",
                        "message": "No matching SIM found",
                        "data": []
                    },
                    status=status.HTTP_200_OK
                )

            serializer = SimprepaidSerializer(sims, many=True)
            if sim_no and sim_no.isdigit() and len(sim_no) == 19:
                simnos = [
                    {"simno": item["simno"]}
                    for item in serializer.data
                    if item["simno"] == sim_no
                ]
            else:
                simnos = [{"simno": item["simno"]} for item in serializer.data]

            return Response(
                {
                    "status": "success",
                    "message": f"{len(simnos)} SIM(s) found",
                    "data": simnos
                },
                status=status.HTTP_200_OK
            )

            # Return only simno list (clean output)
            # simnos = [{"simno": item["simno"]} for item in serializer.data]

            # return Response(
            #     {
            #         "status": "success",
            #         "message": f"{len(simnos)} SIM(s) found",
            #         "data": simnos
            #     },
            #     status=status.HTTP_200_OK
            # )

    except Exception as e:
        return Response(
            {
                "status": "failure",
                "message": "Internal server error",
                "error": str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


    # try:
        # Query logic:
        # sim = Simprepaid.objects.get(
        #     status=1,
        #     location=vendor_code,
        #     simno__endswith=last5
        # )

    #     with transaction.atomic():
    #         sim = Simprepaid.objects.get(
    #         status=1,
    #         location=vendor_code,
    #         simno__endswith=last5
    #     )
    #     serializer = SimprepaidSerializer(sim)
    #     simno = {'simno': serializer.data["simno"]}
    #     return Response(
    #         {
                
    #             'status': "success",
    #             "message": "SIM found",
    #             "data": simno
    #         },
    #         status=status.HTTP_200_OK
    #     )

    # except Simprepaid.DoesNotExist:
    #     return Response(
    #         {
    #             'status': "failure",
    #             "message": "No matching SIM found",
    #             "data": None
    #         },
    #         status=status.HTTP_200_OK
    #     )

    # except Exception as e:
    #     return Response(
    #         {
    #             'status': "failure",
    #             "message": f"Error: {str(e)}",
    #             "data": None
    #         },
    #         status=status.HTTP_500_INTERNAL_SERVER_ERROR
    #     )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_gsm_nos(request):
    """
    Expected POST:
    {
        "circle_code": "102"
    }
    """

    circle_code = request.data.get('circle_code', '').strip()

    # Validate input
    if not circle_code or not circle_code.isdigit():
        return Response(
            {
                'status': "failure",
                "message": "A valid numeric 'circle_code' is required",
                "data": None
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    now_ts = timezone.now()
    try:
        qs = (
        GsmChoice.objects.using("read")
        .filter(
            status=9,
            circle_code=int(circle_code)
        )
        .filter(
            Q(reserve_end_date__isnull=True) |
            Q(reserve_end_date__lt=now_ts)
        )
    )
    #     qs = (
    #     GsmChoice.objects.using("read")
    #     .filter(status=9, circle_code=int(circle_code))
    # )

        count = qs.count()

        if count == 0:
            return Response(
                {"status": "failure", "message": "No records found", "data": []},
                status=404
            )

        offset = random.randint(0, max(count - 20, 0))

        records = qs[offset:offset + 20]

        # records = GsmChoice.objects.filter(
        #     status=9,
        #     circle_code=int(circle_code)
        # ).order_by('?')[:20]


        if not records.exists():
            return Response(
                {
                    'status': "failure",
                    'message': "No matching GSM_CHOICE records found",
                    'data': None
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = GsmChoiceSerializer(records, many=True)
        gsm_list = [item["gsmno"] for item in serializer.data]
        return Response(
            {
                'status': "success",
                "message": "Records found",
                "data": gsm_list
            },
            status=status.HTTP_200_OK
        )

    except Exception as e:
        return Response(
            {
                'status': "failure",
                "message": f"Error: {str(e)}",
                "data": None
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_gsm_status(request):
    """
    Expected POST:
    {
        "gsmno": "9876543210"
    }
    """

    gsmno = request.data.get("gsmno", "").strip()

    if not gsmno:
        return Response(
            {
                "status": "failure",
                "message": "gsmno is required"
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        with transaction.atomic():
            updated = GsmChoice.objects.filter(
                gsmno=gsmno,
                status=9   # ONLY update if status is 9
            ).update(
                status=99,
                trans_date=timezone.now()
            )

            if updated == 0:
                return Response(
                    {
                        "status": "failure",
                        "message": "GSM not found or already processed"
                    },
                    status=status.HTTP_409_CONFLICT
                )

        return Response(
            {
                "status": "success",
                "message": f"GSM {gsmno} updated successfully"
            },
            status=status.HTTP_200_OK
        )

    except Exception as e:
        return Response(
            {"status": "failure", "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    ###############################################################################################
    # try:
    #     # Fetch GSM record
    #     record = GsmChoice.objects.get(gsmno=gsmno)

    #     # Allow update ONLY if current status is 6
    #     if record.status != 9:
    #         return Response(
    #             {
    #                 "status": "failure",
    #                 "message": f"Cannot update. Already Reserved"
    #             },
    #             status=status.HTTP_400_BAD_REQUEST
    #         )

    #     # Update fields
    #     record.status = 99
    #     record.trans_date = timezone.now()

    #     record.save(update_fields=["status", "trans_date"])

    #     return Response(
    #         {
    #             "status": "success",
    #             "message": f"GSM {gsmno} updated successfully"
    #         },
    #         status=status.HTTP_200_OK
    #     )

    # except GsmChoice.DoesNotExist:
    #     return Response(
    #         {
    #             "status": "failure",
    #             "message": "GSM number not found"
    #         },
    #         status=status.HTTP_404_NOT_FOUND
    #     )

    # except Exception as e:
    #     return Response(
    #         {
    #             "status": "failure",
    #             "message": f"Error: {str(e)}"
    #         },
    #         status=status.HTTP_500_INTERNAL_SERVER_ERROR
    #     )



@api_view(['POST'])
def refresh_token(request):
    """
    Refresh JWT token
    
    Expected POST data:
    {
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
    }
    """
    refresh_token = request.data.get('refresh')
    
    if not refresh_token:
        return Response(
            {'success': False, 'message': 'Refresh token required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        refresh = RefreshToken(refresh_token)
        return Response(
            {
                'success': True,
                'access_token': str(refresh.access_token),
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return Response(
            {'success': False, 'message': 'Invalid refresh token'},
            status=status.HTTP_401_UNAUTHORIZED
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_app_version(request):
    try:
        # Fetch the latest version (assuming last inserted is latest)
        version_obj = AppVersion.objects.order_by('-id').first()

        if not version_obj:
            return Response(
                {
                    "status": "failure",
                    "message": "Version not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AppVersionSerializer(version_obj)

        return Response(
            {
                "status": "success",
                "version": serializer.data['version']
            },
            status=status.HTTP_200_OK
        )

    except Exception as e:
        return Response(
            {
                "status": "failure",
                "message": f"Error: {str(e)}"
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_aadhaar(request):
    """
    Update Aadhaar number based on CTOP UP number.

    Expected POST:
    {
        "ctopupno": "9447001122",
        "aadhaar_no": "123412341234"
    }
    """
    
    ctopupno = request.data.get("ctopupno", "").strip()
    aadhaar_no = request.data.get("aadhaar_no", "").strip()

    # Validate CTOP number
    if not ctopupno:
        return Response(
            {"status": "failure", "message": "Username  is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validate Aadhaar
    if not aadhaar_no or len(aadhaar_no) != 12 or not aadhaar_no.isdigit():
        return Response(
            {"status": "failure", "message": "Invalid Aadhaar number. Must be 12 digits."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Check CTOP user exists
        ctop = CtopMaster.objects.get(username=ctopupno)

        # Update Aadhaar number
        ctop.aadhaar_no = aadhaar_no
        ctop.save(update_fields=["aadhaar_no"])
                            

        return Response(
            {
                "status": "success",
                "message": "Aadhaar number updated successfully",
                "data":{
                    'ctopup_number':ctop.username,
                    'name': ctop.name,
                    'vendor_code':ctop.attached_to,
                    'circle_code':str(ctop.circle_code),
                    'aadhaar_no':aadhaar_no
                    }
            },
            status=status.HTTP_200_OK
        )

    except CtopMaster.DoesNotExist:
        return Response(
            {"status": "failure", "message": "CTOP UP number not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    except Exception as e:
        return Response(
            {"status": "failure", "message": f"Error: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def adhar_api_forward(request):
    url = "http://10.201.217.124:9010/api/ekyc-authenticate"

    payload = request.data   # <--- FIXED

    try:
        response = requests.post(url, json=payload, timeout=30)
    except requests.exceptions.RequestException as e:
        return Response(
            {"status": "failure", "message": f"Network error: {str(e)}"},
            status=500
        )

    # Safe JSON extraction
    try:
        response_payload = response.json()
    except ValueError:
        return Response(
            {"status": "failure", "message": "Invalid JSON from Aadhaar API"},
            status=500
        )

    return Response(response_payload, status=response.status_code)


@api_view(["POST"])
def resend_otp(request):
    mobile = request.data.get("ctopupno")

    if not mobile:
        return Response({"status": "error", "message": "Mobile number required"}, status=400)

    # Check last OTP (optional cooldown of 30 seconds)
    last_otp = ApiOtpTable.objects.filter(ctopupno=mobile).order_by("-created_at").first()

    if last_otp:
        elapsed = timezone.now() - last_otp.created_at
        if elapsed < timedelta(seconds=30):
            return Response({
                "status": "error",
                "message": "Please wait before resending OTP.",
                "wait_seconds": 30 - int(elapsed.total_seconds())
            }, status=429)
        elif elapsed < timedelta(minutes=10):
            resend_sms(mobile, last_otp.otp)

    # Generate new OTP
    otp = str(random.randint(100000, 999999))

    # Save in DB
    ApiOtpTable.objects.create(
        ctopupno=mobile,
        otp=otp
    )

    # Send SMS
    resend_sms(mobile, otp)

    return Response({
        "status": "success",
        "message": "OTP resent successfully",
        "mobileno": mobile
    },status=200)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def local_ref_otp(request):
    mobile = request.data.get("ref_number")

    if not mobile:
        return Response({"status": "error", "message": "Mobile number required"}, status=400)

    # Generate new OTP
    otp = str(random.randint(100000, 999999))

    # Save in DB
    RefOtpTable.objects.create(
        refno=mobile,
        otp=otp
    )

    # Send SMS
    ref_send_sms(mobile, otp)

    return Response({
        "status": "success",
        "message": "OTP Send successfully",
        "mobileno": mobile
    },status=200)




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def local_ref_otp_verfiy(request):

    refno = request.data.get('ref_number', '').strip()
    otp = request.data.get('ref_otp', '').strip()

    # Validate required fields
    if not refno or not otp:
        return Response(
            {
                'status': "failure",
                'message': 'CTOP UP number and OTP are required',
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Verify OTP
        otp_record = RefOtpTable.objects.filter(
            refno=refno,
            otp=otp
        ).order_by('-created_at').first()

        otp_age = (timezone.now() - otp_record.created_at).total_seconds()
        if otp_age > 600:  # 10 minutes
            # Delete expired OTP
            otp_record.delete()
            return Response(
                {
                    'status': "failure",
                    'message': 'OTP has expired. Please request a new one.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
       
        if otp_record:
            # SUCCESS
            return Response(
                {
                    'status': "success",
                    'message': 'OTP verified successfully',
                    'ref_number':refno,
                    'ref_otp':otp,
                    'ref_timestamp': otp_record.created_at
                },
                status=status.HTTP_200_OK
            )

        # OTP not found or incorrect
        return Response(
            {
                'status': "failure",
                'message': 'Invalid OTP'
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    except Exception as e:
        return Response(
            {
                'status': "failure",
                'message': f'Error: {str(e)}'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_verification_status(request):
    try:
        username = request.data.get("ctopupno")
        status_param = request.data.get("caf_status")

        if not username or not status_param:
            return Response(
                {
                    "status": "failure",
                    "message": "username and status are required"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Map request status to database values
        status_mapping = {
            "caf_pending": None,  # NULL or empty in database
            "caf_active": "Y",
            "caf_rejected": "R",
            "caf_see_later": "F"  # F = see later/deferred
        }

        status_param = status_mapping.get(status_param, "INVALID")

        if status_param == "INVALID":
            return Response(
                {
                    "status": "failure",
                    "message": "Invalid status. Use caf_pending, caf_active, caf_rejected, or caf_see_later"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Filter records - handle NULL case
        if status_param is None:
            records = CosBcd.objects.filter(
                de_username=username,
                verified_flag__isnull=True
            ) | CosBcd.objects.filter(
                de_username=username,
                verified_flag=""
            )
            dkyc_records = CosBcdDkyc.objects.filter(
                de_username=username,
                verified_flag__isnull=True
            ) | CosBcdDkyc.objects.filter(
                de_username=username,
                verified_flag=""
            )
        else:
            records = CosBcd.objects.filter(
                de_username=username,
                verified_flag=status_param
            )
            dkyc_records = CosBcdDkyc.objects.filter(
                de_username=username,
                verified_flag=status_param
            )
        #records = list(chain(records, dkyc_records))
        if not records.exists() and not dkyc_records.exists():
            return Response(
                {
                    "count": 0,
                    "records": []
                },
                status=status.HTTP_200_OK
            )
        records = list(chain(records, dkyc_records))
        # Build list of response objects
        result_list = []
        current_time = timezone.now().isoformat()

        status_map = {
            "Y": "approved",
            "R": "rejected",
            "F": "see_later",
        }

        for rec in records:
            vf = (rec.verified_flag or "").strip().upper()

            # If NULL/empty → pending, otherwise map
            status_value = status_map.get(vf, "pending")

            item = {
                "caf_id": getattr(rec, "caf_serial_no", None),
                "mobileno": rec.gsmnumber,
                "simnumber": getattr(rec, "simnumber", None) or getattr(rec, "sim_no", None),
                "caf_type" : rec.caf_type,
                "category": "prepaid" if int(getattr(rec, "connection_type", 1) or 1) == 1 else "postpaid",
                "time_act": (
                        (
                            getattr(rec, "verified_date", None)
                            or getattr(rec, "live_photo_time", None)
                            or getattr(rec, "created_at", None)
                        ).isoformat()
                        if (
                            getattr(rec, "verified_date", None)
                            or getattr(rec, "live_photo_time", None)
                            or getattr(rec, "created_at", None)
                        )
                        else None
                    ),
                "status": status_value,
                "rejection_reason": getattr(rec, "rejection_reason", None) or ""
            }

            if rec.caf_type == "mnp":
                item["upccode"] = getattr(rec, "upc_code", None)
                item["upcValidupto"] = (
                    rec.upcvalidupto.isoformat()
                    if getattr(rec, "upcvalidupto", None)
                    else None
                )

            result_list.append(item)
        result_list.sort(
            key=lambda x: x["time_act"] if x["time_act"] else "",
            reverse=True
        )
        return Response(
            {
                "count": len(result_list),
                "records": result_list
            },
            status=status.HTTP_200_OK
        )

    except Exception as e:
        return Response(
            {"status": "failure", "message": f"Error: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])  # Heartbeat usually doesn't require auth
def heartbeat(request):
    return Response({
        "status": "ok",
        "message": "Service healthy",
        "time": timezone.now()
    }, status=200)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_frc_plans(request):
    try:
        circle = request.data.get("circle_code")

        if not circle:
            return Response({
                "status": "error",
                "message": "circle_code is required"
            }, status=400)

        # # Circle-specific plans (active only)
        # circle_plans = FrcPlan.objects.filter(
        #     circle_code=circle,
        #     end_date__isnull=True
        # )

        # # Common plans (circle 9999, active only)
        # common_plans = FrcPlan.objects.filter(
        #     circle_code="9999",
        #     end_date__isnull=True
        # )

        # # Combine both
        # plans = list(circle_plans) + list(common_plans)

                # Active plans: circle-specific + common (9999)
        today = timezone.localdate()
        plans = FrcPlan.objects.filter(
            start_date__lte=today
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=today)
        ).filter(
            Q(circle_code=circle) | Q(circle_code="9999")
        )

        result = [
            {
                "plan_name": p.plan_name,
                "plan_code": p.plan_code,
                "category_code": p.category_code,
            }
            for p in plans
        ]

        return Response({
            "status": "success",
            "count": len(result),
            "plans": result
        }, status=200)

    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=500)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_postpaid_plans(request):
    try:
        circle = request.data.get("circle_code")

        if not circle:
            return Response({
                "status": "error",
                "message": "circle_code is required"
            }, status=400)

        # Get PLANS for passed circle
        circle_plans = PostpaidPlansApp.objects.filter(circle_code=circle)

        # Get COMMON PLANS (circle 9999)
        common_plans = PostpaidPlansApp.objects.filter(circle_code="9999")

        # Combine both
        plans = list(circle_plans) + list(common_plans)

        result = [
            {
                "plan_name": p.plan_name

            }
            for p in plans
        ]

        return Response({
            "status": "success",
            "count": len(result),
            "plans": result
        }, status=200)

    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=500)
    



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_vrf_status(request):
    try:
        # ------------------------------------------------
        # 1️⃣ Read request payload
        # ------------------------------------------------
        username = request.data.get("ctopupno")
        caf_status = request.data.get("caf_status")

        if not username or not caf_status:
            return Response(
                {
                    "status": "failure",
                    "message": "ctopupno and caf_status are required"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        caf_status = caf_status.strip().lower()

        # ------------------------------------------------
        # 2️⃣ Validate caf_status
        # ------------------------------------------------
        allowed_statuses = {
            "caf_pending",
            "caf_active",
            "caf_rejected",
            "caf_see_later"
        }

        if caf_status not in allowed_statuses:
            return Response(
                {
                    "status": "failure",
                    "message": (
                        "Invalid caf_status. "
                        "Use caf_pending, caf_active, caf_rejected, or caf_see_later"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ------------------------------------------------
        # 3️⃣ Build queryset (NO UNION, NO LEAKAGE)
        # ------------------------------------------------
        if caf_status == "caf_pending":
            # Pending = NULL or empty
            records = CosBcd.objects.filter(
                de_username=username
            ).filter(
                Q(verified_flag__isnull=True) | Q(verified_flag="")
            )

        elif caf_status == "caf_active":
            records = CosBcd.objects.filter(
                de_username=username,
                verified_flag="Y"
            )

        elif caf_status == "caf_rejected":
            records = CosBcd.objects.filter(
                de_username=username,
                verified_flag="R"
            )

        elif caf_status == "caf_see_later":
            records = CosBcd.objects.filter(
                de_username=username,
                verified_flag="F"
            )

        # ------------------------------------------------
        # 4️⃣ Empty result handling
        # ------------------------------------------------
        if not records.exists():
            return Response(
                {
                    "count": 0,
                    "records": []
                },
                status=status.HTTP_200_OK
            )

        # ------------------------------------------------
        # 5️⃣ Build response
        # ------------------------------------------------
        status_map = {
            "Y": "approved",
            "R": "rejected",
            "F": "see_later"
        }

        result_list = []

        for rec in records:
            vf = (rec.verified_flag or "").strip().upper()

            item = {
                "caf_id": getattr(rec, "caf_serial_no", None),
                "mobileno": rec.gsmnumber,
                "simnumber": getattr(rec, "simnumber", None),
                "caf_type": rec.caf_type,
                "category": (
                    "prepaid"
                    if getattr(rec, "connection_type", 1) == 1
                    else "postpaid"
                ),
                "time_act": (
                    rec.verified_date.isoformat()
                    if rec.verified_date
                    else (
                        rec.live_photo_time.isoformat()
                        if rec.live_photo_time
                        else None
                    )
                ),
                "status": status_map.get(vf, "pending"),
                "rejection_reason": rec.rejection_reason or ""
            }

            result_list.append(item)

        # ------------------------------------------------
        # 6️⃣ Final response
        # ------------------------------------------------
        return Response(
            {
                "count": len(result_list),
                "records": result_list
            },
            status=status.HTTP_200_OK
        )

    except Exception as e:
        return Response(
            {
                "status": "failure",
                "message": f"Internal error: {str(e)}"
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def release_sim(request):
    """
    Release SIM from SOLD pool back to AVAILABLE pool
    """

    simnumber = request.data.get("simnumber")
    category = request.data.get("category")   # prepaid / postpaid
    caf_id = request.data.get("caf_id")
    non_rejected_exists = CosBcd.objects.filter(
                simnumber=simnumber
                ).exclude(
                    verified_flag='R'
                ).exists()

    if non_rejected_exists:
        return Response(
            {
                "status": "failure",
                "message": "SIM cannot be released. One or more CAF records are not rejected."
            },
            status=status.HTTP_200_OK
        )

    if not simnumber or not category:
        return Response(
            {
                "status": "failure",
                "message": "simnumber and category are required"
            },
            status=status.HTTP_200_OK
        )

    category = category.strip().lower()

    if category not in ("prepaid", "postpaid"):
        return Response(
            {
                "status": "failure",
                "message": "category must be prepaid or postpaid"
            },
            status=status.HTTP_200_OK
        )

    try:
        with transaction.atomic():

            # ----------------------------
            # POSTPAID
            # ----------------------------
            if category == "postpaid":
                sold_obj = (
                    SimpostpaidSold.objects
                    .filter(simno=simnumber)
                    .first()
                )

                if not sold_obj:
                    return Response(
                        {
                            "status": "failure",
                            "message": "SIM Already Released"
                        },
                        status=status.HTTP_200_OK
                    )

                data = model_to_dict(sold_obj)
                data.pop("id", None)  # remove PK
                data["changed_date"] = timezone.now()
                # Prevent duplicate insert
                if Simpostpaid.objects.filter(simno=simnumber).exists():
                    return Response(
                        {
                            "status": "failure",
                            "message": "SIM already available in postpaid pool"
                        },
                        status=status.HTTP_200_OK
                    )

                Simpostpaid.objects.create(**data)
                sold_obj.delete()

            # ----------------------------
            # PREPAID
            # ----------------------------
            else:
                sold_obj = (
                    SimprepaidSold.objects
                    .filter(simno=simnumber)
                    .first()
                )

                if not sold_obj:
                    return Response(
                        {
                            "status": "failure",
                            "message": "SIM Already Released"
                        },
                        status=status.HTTP_200_OK
                    )

                data = model_to_dict(sold_obj)
                data.pop("id", None)
                data["changed_date"] = timezone.now()
                if Simprepaid.objects.filter(simno=simnumber).exists():
                    return Response(
                        {
                            "status": "failure",
                            "message": "SIM already available in prepaid pool"
                        },
                        status=status.HTTP_409_CONFLICT
                    )

                Simprepaid.objects.create(**data)
                sold_obj.delete()

        return Response(
            {
                "status": "success",
                "message": "SIM released successfully",
                "simnumber": simnumber,
                "category": category,
                "caf_id": caf_id
            },
            status=status.HTTP_200_OK
        )

    except Exception as e:
        return Response(
            {
                "status": "failure",
                "message": f"Error releasing SIM: {str(e)}"
            },
            status=status.HTTP_200_OK
        )

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upgradation_send_otp(request):
    gsmno = request.data.get("gsmno", "").strip()

    if not gsmno:
        return Response(
            {"status": "error", "message": "GSM number required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Generate OTP
    otp = str(random.randint(100000, 999999))

    # Save OTP
    UpgradationOtpTable.objects.create(
        gsmnno=gsmno,
        otp=otp
    )

    # Send SMS
    upg_send_sms(gsmno, otp)

    return Response(
        {
            "status": "success",
            "message": "OTP sent successfully",
            "gsmno": gsmno
        },
        status=status.HTTP_200_OK
    )

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upgradation_verify_otp(request):

    gsmno = request.data.get("gsmno", "").strip()
    otp = request.data.get("otp", "").strip()

    if not gsmno or not otp:
        return Response(
            {
                "status": "failure",
                "message": "GSM number and OTP are required"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        otp_record = UpgradationOtpTable.objects.filter(
            gsmnno=gsmno,
            otp=otp
        ).order_by("-created_at").first()

        if not otp_record:
            return Response(
                {
                    "status": "failure",
                    "message": "Invalid OTP"
                },
                status=status.HTTP_200_OK
            )

        # Check expiry (10 minutes)
        otp_age = (timezone.now() - otp_record.created_at).total_seconds()
        if otp_age > 600:
            otp_record.delete()
            return Response(
                {
                    "status": "failure",
                    "message": "OTP has expired. Please request a new one."
                },
                status=status.HTTP_200_OK
            )

        return Response(
            {
                "status": "success",
                "message": "OTP verified successfully",
                "gsmno": gsmno,
                "otp": otp,
                "verified_at": otp_record.created_at
            },
            status=status.HTTP_200_OK
        )

    except Exception as e:
        return Response(
            {
                "status": "failure",
                "message": f"Error: {str(e)}"
            },
            status=status.HTTP_200_OK
        )

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upgradation_resend_otp(request):

    gsmno = request.data.get("gsmno", "").strip()

    if not gsmno:
        return Response(
            {"status": "error", "message": "GSM number required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check last OTP (30 sec cooldown)
    last_otp = UpgradationOtpTable.objects.filter(
        gsmnno=gsmno
    ).order_by("-created_at").first()

    if last_otp:
        elapsed = timezone.now() - last_otp.created_at
        if elapsed < timedelta(seconds=30):
            return Response(
                {
                    "status": "error",
                    "message": "Please wait before resending OTP.",
                    "wait_seconds": 30 - int(elapsed.total_seconds())
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

    # Generate new OTP
    otp = str(random.randint(100000, 999999))

    # Save new OTP
    UpgradationOtpTable.objects.create(
        gsmnno=gsmno,
        otp=otp
    )

    # Send SMS
    ref_send_sms(gsmno, otp)

    return Response(
        {
            "status": "success",
            "message": "OTP resent successfully",
            "gsmno": gsmno
        },
        status=status.HTTP_200_OK
    )

############################################################################################################
############################# CAF DEDUP CHECK ##############################################################
@api_view(["POST"])
def check_gsm_caf(request):

    gsmno = request.data.get("gsmno")
    caf_type = request.data.get("caf_type")

    if not gsmno or not caf_type:
        return Response(
            {
                "status": "failure",
                "message": "gsmno and caf_type are required"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    records = CosBcd.objects.filter(gsmnumber=gsmno)

    # Case 1: No CAF at all
    if not records.exists():
        return Response(
            {
                "status": "success",
                "Allow": "Yes",
                "gsmno": gsmno,
                "caf_type": caf_type,
                "Reason": "No existing CAF found"
            },
            status=status.HTTP_200_OK
        )

    # Case 2: Verified CAF exists
    verified_record = records.filter(
        caf_type=caf_type,
        verified_flag='Y'
    ).order_by('-verified_date').first()

    if verified_record:
        return Response(
            {
                "status": "success",
                "Allow": "No",
                "gsmno": gsmno,
                "caf_type": caf_type,
                "Reason": "CAF already exists and verified",
                "Date of Verification": verified_record.verified_date
            },
            status=status.HTTP_200_OK
        )

    # Case 3: CAF exists but not verified
    pending_record = records.filter(
        caf_type=caf_type,
        verified_flag__isnull=True
    ).order_by('-live_photo_time').first()

    if pending_record:
        return Response(
            {
                "status": "success",
                "Allow": "No",
                "gsmno": gsmno,
                "caf_type": caf_type,
                "Reason": "CAF already exists and pending verification"
            },
            status=status.HTTP_200_OK
        )

    # Case 4: CAF exists but for different caf_type
    other_record = records.exclude(
        caf_type=caf_type
    ).order_by('-live_photo_time').first()
    if other_record:
        return Response(
            {
                "status": "success",
                "Allow": "Yes",
                "gsmno": gsmno,
                "caf_type": other_record.caf_type,
                "Reason": "CAF exists for different caf_type"
            },
            status=status.HTTP_200_OK
        )
    return Response(
        {
            "status": "success",
            "Allow": "Yes",
            "gsmno": gsmno,
            "caf_type": caf_type,
            "Reason": "CAF exists, Caf Rejected "
        },
        status=status.HTTP_200_OK
    )
##########################################################################################################
####################### Adhaar Check #####################################################################

@api_view(["POST"])
def check_aadhaar_onboarding(request):

    customer_aadhaar = request.data.get("customer_aadhaar")
    circle_code = request.data.get("circle_code")
    if not customer_aadhaar:
        return Response({
            "status": "error",
            "message": "aadhaar is required"
        }, status=200)
    #####################check aadhaar #######################
    exists, previous_gsm = is_sim_allotted_today(customer_aadhaar, circle_code)
    if not exists:
        return Response(
            {
                "status": "success",
                "Allow": "Yes",
                "Reason": "Aadhaar not used today"
            },
            status=200
        )
    caf = CosBcd.objects.filter(
        gsmnumber=previous_gsm
    ).order_by('-live_photo_time').first()

    if caf.verified_flag =='R':
        return Response(
            {
                "status": "success",
                "Allow": "Yes",
                "Reason": "Caf Rejected"
            },
            status=200
        )
    else:
        return Response({
            "status": "failed",
            "Allow": "No",
            "message": "SIM already allotted within restriction window",
            "previous_gsm": previous_gsm
        }, status=200)


 

    

