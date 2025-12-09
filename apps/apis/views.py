# views.py
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import CtopMaster,Simprepaid, Simpostpaid, GsmChoice ,ApiOtpTable, AppVersion,RefOtpTable,CosBcd
from .serializers import CtopMasterSerializer,SimprepaidSerializer,SimpostpaidSerializer,GsmChoiceSerializer,AppVersionSerializer
import random
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.cache import cache
from .send_sms import send_sms, ref_send_sms
from django.utils import timezone
from datetime import datetime, timedelta
import requests,json
import time
from django.utils.timezone import now


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
        ctop = CtopMaster.objects.get(username=ctopupno)
        t2 = time.time()
        # If found, return success with data
        serializer = CtopMasterSerializer(ctop)
        t3 = time.time()
        otp = str(random.randint(100000, 999999))
        
        # Save OTP in database
        ApiOtpTable.objects.create(
            ctopupno=ctop.ctopupno,
            otp=otp
        )
        t4 = time.time()
        send_sms(ctop.ctopupno,otp)
        t5 = time.time()
        total = t5 - t0
        print(f"""
            --- Timing Breakdown ---
            Input validation: {t1 - t0:.4f}s
            ORM fetch:        {t2 - t1:.4f}s
            Serialization:    {t3 - t2:.4f}s
            OTP Insert:       {t4 - t3:.4f}s
            SMS Send:         {t5 - t4:.4f}s
            TOTAL:            {total:.4f}s
            """)
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
        CtopMaster.objects.get(username=ctopupno)

        # Verify OTP
        otp_record = ApiOtpTable.objects.filter(
            ctopupno=ctopupno,
            otp=otp
        ).order_by('-created_at').first()

        # otp_age = (timezone.now() - otp_record.created_at).total_seconds()
        # if otp_age > 600:  # 10 minutes
        #     # Delete expired OTP
        #     otp_record.delete()
        #     return Response(
        #         {
        #             'status': "failure",
        #             'message': 'OTP has expired. Please request a new one.'
        #         },
        #         status=status.HTTP_400_BAD_REQUEST
        #     )

        ctop = CtopMaster.objects.get(username=ctopupno)

        brute_force_key = f"login_attempts_{ctopupno}"

        # Create refresh token
        refresh = RefreshToken()  # <-- IMPORTANT CHANGE

        refresh['exp'] = int((timezone.now() + timedelta(days=7)).timestamp())
        refresh['iat'] = int(timezone.now().timestamp())
        refresh['token_type'] = 'refresh'

        # Add custom claims
        refresh['ctopupno'] = ctop.ctopupno
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
            return Response(
                {
                    'status': "success",
                    'message': 'OTP verified successfully',
                    'access_token':str(access_token),
                    'refresh_token':str(refresh),
                    'data':{
                    'ctopup_number':ctop.ctopupno,
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
            status=status.HTTP_400_BAD_REQUEST
        )

    except CtopMaster.DoesNotExist:
        return Response(
            {
                'status': "failure",
                'message': 'CTOP UP number does not exist',
            },
            status=status.HTTP_404_NOT_FOUND
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
    {
        "last5": "12345",
        "vendor_code": "V001"
    }
    """
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
        # Query logic:
        sim = Simpostpaid.objects.get(
            status=1,
            location=vendor_code,
            simno__endswith=last5
        )

        serializer = SimpostpaidSerializer(sim)
        simno = {'simno': serializer.data["simno"]}

        return Response(
            {
                
                'status': "success",
                "message": "SIM found",
                "data": simno
            },
            status=status.HTTP_200_OK
        )

    except Simpostpaid.DoesNotExist:
        return Response(
            {
                'status': "failure",
                "message": "No matching SIM found",
                "data": None
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
def get_prepaid(request):
    """
    Expected POST:
    {
        "last5": "12345",
        "vendor_code": "V001"
    }
    """
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
        # Query logic:
        sim = Simprepaid.objects.get(
            status=1,
            location=vendor_code,
            simno__endswith=last5
        )

        serializer = SimprepaidSerializer(sim)
        simno = {'simno': serializer.data["simno"]}
        return Response(
            {
                
                'status': "success",
                "message": "SIM found",
                "data": simno
            },
            status=status.HTTP_200_OK
        )

    except Simprepaid.DoesNotExist:
        return Response(
            {
                'status': "failure",
                "message": "No matching SIM found",
                "data": None
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

    try:

        records = GsmChoice.objects.filter(
            status=9,
            circle_code=int(circle_code)
        ).order_by('?')[:20]
                # Fetch matching GSM_CHOICE rows
        # records = GsmChoice.objects.filter(
        #     status=6,
        #     circle_code=int(circle_code)
        # )[:50]

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
        # Fetch GSM record
        record = GsmChoice.objects.get(gsmno=gsmno)

        # Allow update ONLY if current status is 6
        if record.status != 9:
            return Response(
                {
                    "status": "failure",
                    "message": f"Cannot update. Already Reserved"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update fields
        record.status = 99
        record.trans_date = timezone.now()

        record.save(update_fields=["status", "trans_date"])

        return Response(
            {
                "status": "success",
                "message": f"GSM {gsmno} updated successfully"
            },
            status=status.HTTP_200_OK
        )

    except GsmChoice.DoesNotExist:
        return Response(
            {
                "status": "failure",
                "message": "GSM number not found"
            },
            status=status.HTTP_404_NOT_FOUND
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
            {"status": "failure", "message": "CTOP UP number is required"},
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
        ctop = CtopMaster.objects.get(ctopupno=ctopupno)

        # Update Aadhaar number
        ctop.aadhaar_no = aadhaar_no
        ctop.save(update_fields=["aadhaar_no"])
                            

        return Response(
            {
                "status": "success",
                "message": "Aadhaar number updated successfully",
                "data":{
                    'ctopup_number':ctop.ctopupno,
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

    # Generate new OTP
    otp = str(random.randint(100000, 999999))

    # Save in DB
    ApiOtpTable.objects.create(
        ctopupno=mobile,
        otp=otp
    )

    # Send SMS
    send_sms(mobile, otp)

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

    except CtopMaster.DoesNotExist:
        return Response(
            {
                'status': "failure",
                'message': 'CTOP UP number does not exist',
            },
            status=status.HTTP_404_NOT_FOUND
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
        status_param= None
        # Filter records
        records = CosBcd.objects.filter(
            de_username=username,
            verified_flag=status_param
        )

        if not records.exists():
            return Response(
                {
                    "status": "failure",
                    "message": "No records found for this username and status"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # Build list of response objects
        result_list = []
        current_time = timezone.now().isoformat()

        for rec in records:
            item = {
                "caf_id": getattr(rec, "caf_serial_no", None),
                "mobileno": rec.gsmnumber,
                "simnumber": getattr(rec, "simnumber", None),
                "category": "prepaid" if getattr(rec, "category", 1) == 1 else "postpaid",
                "time_act": current_time,
                "status": "pending" 
                #if rec.verified_flag == "0" else "approved",
            }
            result_list.append(item)

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