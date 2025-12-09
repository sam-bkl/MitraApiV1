from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import CosBcd,GsmChoice,Simprepaid,Simpostpaid
from .serializers import CosBcdSerializer
import random
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.cache import cache
from .send_sms import send_sms
from django.utils import timezone
from datetime import datetime, timedelta
import base64,os
from . import create_cafid
from datetime import datetime



# print('ssss',create_cafid.get_caf_id())

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_caf_details(request):
    ### get IP ###
    # 1. Retrieve raw header values from request.META
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    x_real_ip = request.META.get('HTTP_X_REAL_IP')
    remote_addr = request.META.get('REMOTE_ADDR') # The direct connecting IP

    # 2. Logic to determine the "Actual" Client IP
    # Priority: X-Forwarded-For (first IP) -> X-Real-IP -> REMOTE_ADDR
    if x_forwarded_for:
        # X-Forwarded-For can be a comma-separated list like "client, proxy1, proxy2"
        # We take the first one as the true client
        actual_ip = x_forwarded_for.split(',')[0].strip()
    elif x_real_ip:
        actual_ip = x_real_ip
    else:
        actual_ip = remote_addr

    ###############

    ctopupno = request.data.get("ctopup_number")
    vendor_code = request.data.get("vendorcode")
    circle_code = request.data.get("circle_code")
    mobileno = request.data.get("mobileno")
    pwd = request.data.get("pwd")
    connection_type = request.data.get("connection_type")
    subscriber_type = request.data.get("subscriber_type")
    simno = request.data.get("simno")
    poi = request.data.get("Poi", {})
    poa = request.data.get("Poa", {})
    pht = request.data.get("Pht")
    cst_unique_code = request.data.get("cst_unique_code")
    cst_res_timestamp = request.data.get("cst_res_timestamp")
    posUid = request.data.get("posUid", {})
    posPoi = request.data.get("posPoi", {})
    posPoa = request.data.get("posPoa", {})
    posPht = request.data.get("posPht")
    pos_unique_code = request.data.get("pos_unique_code")
    pos_res_timestamp = request.data.get("pos_res_timestamp")
    father_husband_name = request.data.get("father_husband_name")
    masked_adhar= request.data.get("masked_adhar")
    nationality = request.data.get("nationality")
    number_of_mobile_connections = request.data.get("number_of_mobile_connections")
    email_id = request.data.get("email_id")
    customer_alternate_mobile_number = request.data.get("customer_alternate_mobile_number")
    subscriber_live_photo = request.data.get("subscriber_live_photo")
    pos_live_photo = request.data.get("pos_live_photo")
    #device_ip = request.data.get("device_ip")
    device_mac = request.data.get("device_mac")
    app_version = request.data.get("app_version")
    current_location = request.data.get("current_location", {})
    lat = current_location.get("lat")
    lng = current_location.get("lng")
    local_reference = request.data.get("local_reference", {})
    photo_base64 = request.data.get("Pht", None)
    upc_code = request.data.get("upc_code")
    upcValidUpto = request.data.get("upcValidUpto")
    caf_type = request.data.get("caf_type")

    decoded_photo = None
    decoded_live_photo = None
    decoded_pos_photo = None
    decoded_pos_ad_photo = None
    if app_version != "1.0.2":
        return Response(
            {"status": "error", "message": "Update required"},
            status=status.HTTP_403_FORBIDDEN
        )

    if photo_base64:
        try:
            decoded_photo = base64.b64decode(photo_base64)
            if decoded_photo is None:
                return Response(
                    {"status": "failure", "message": "Invalid Aadhaar photo"},
                    status=400
                )
        except Exception:
            return Response(
                {"status": "failure", "message": "Invalid base64 Aadhaar photo"},
                status=400
            )
    else:
        return Response(
                    {"status": "failure", "message": "No Aadhaar photo"},
                    status=400
                )
    
    if posPht:
        try:
            decoded_pos_ad_photo = base64.b64decode(posPht)
            if decoded_pos_ad_photo is None:
                return Response(
                    {"status": "failure", "message": "Invalid Aadhaar photo"},
                    status=400
                )
        except Exception:
            return Response(
                {"status": "failure", "message": "Invalid base64 Aadhaar photo"},
                status=400
            )
    else:
        return Response(
                    {"status": "failure", "message": "No Aadhaar photo"},
                    status=400
                )

    
    if subscriber_live_photo:
        try:
            decoded_subscriber_live_photo = base64.b64decode(subscriber_live_photo)
            if decoded_subscriber_live_photo is None:
                return Response(
                    {"status": "failure", "message": "Invalid live photo"},
                    status=400
                )
        except Exception:
            return Response(
                {"status": "failure", "message": "Invalid base64 Aadhaar photo"},
                status=400
            )
    else:
        return Response(
                    {"status": "failure", "message": "No Aadhaar photo"},
                    status=400
                )
    if pos_live_photo:
        try:
            decoded_pos_live_photo = base64.b64decode(pos_live_photo)
            if decoded_pos_live_photo is None:
                return Response(
                    {"status": "failure", "message": "Invalid live photo"},
                    status=400
                )
        except Exception:
            return Response(
                {"status": "failure", "message": "Invalid base64 Aadhaar photo"},
                status=400
            )
    else:
        return Response(
                    {"status": "failure", "message": "No Aadhaar photo"},
                    status=400
                )
    caf_no=create_cafid.get_caf_id()
    today = datetime.now()
    year = today.strftime("%Y")
    month = today.strftime("%m")
    day = today.strftime("%d")

    # base directory
    base_dir = "/cosdata/files/cos_images/"

    # full directory path: /home/bsnlcos/cos_images/YYYY/MM/DD/
    full_dir = os.path.join(base_dir, year, month, day)

    # create folders if not exist
    os.makedirs(full_dir, exist_ok=True)

    # final file path
    
    pos_image_file = f"{caf_no}p.jpg"
    pos_adh_image_file = f"{caf_no}pa.jpg"
    live_image_file = f"{caf_no}l.jpg"
    adh_image_file= f"{caf_no}a.jpg"
    with open(os.path.join(full_dir, adh_image_file), "wb") as f:
        f.write(decoded_photo)
    with open(os.path.join(full_dir, pos_image_file), "wb") as f:
        f.write(decoded_pos_live_photo)
    with open(os.path.join(full_dir, live_image_file), "wb") as f:
        f.write(decoded_subscriber_live_photo)
    with open(os.path.join(full_dir, pos_adh_image_file), "wb") as f:
        f.write(decoded_pos_ad_photo)
    record = CosBcd(caf_serial_no=caf_no)
    if not caf_no:
        return Response({"status": "failure", "message": "caf_serial_no missing"}, status=400)

    # try:
    #     record = CosBcd.objects.get(caf_serial_no=caf_no)
    # except CosBcd.DoesNotExist:
    #     return Response({"status": "failure", "message": "CAF not found"}, status=404)

    # --------------------------
    # Extract POI fields
    # --------------------------
    name = poi.get("@name")
    pos_name_adh = posPoi.get("@name")
    dob_str = poi.get("@dob")
    gender = poi.get("@gender")
    print("email id is ", email_id)
    dob = None
    if dob_str:
        try:
            dob = datetime.strptime(dob_str, "%d-%m-%Y")
        except:
            pass

    # --------------------------
    # Extract POA fields
    # --------------------------
    f_h_name = poa.get("@co")
    house = poa.get("@house")
    landmark = poa.get("@lm")
    locality = poa.get("@locality") or None
    vtc = poa.get("@vtc")
    district = poa.get("@dist")
    state = poa.get("@state")
    pin = poa.get("@pc")

    # --------------------------
    # Update the CosBcd record
    # --------------------------
    record.de_csccode=vendor_code
    record.de_username=ctopupno 
    record.gsmnumber= mobileno
    record.simnumber= simno
    record.caf_serial_no= caf_no
    if connection_type=="postpaid":
        record.connection_type=2
    else:
        record.connection_type=1

    ####################### extract local reference fields ###########################
    ref_name = local_reference.get("ref_name")
    ref_mobile = local_reference.get("ref_mobile_number")
    ref_address = local_reference.get("ref_address")
    ref_otp = local_reference.get("ref_otp")
    ref_otp_timestamp = local_reference.get("ref_otp_timestamp")
    ref_careof = local_reference.get("ref_careof_address")
    ref_house = local_reference.get("ref_house_name_no")
    ref_street = local_reference.get("ref_street_address")
    ref_landmark = local_reference.get("ref_landmark")
    ref_area = local_reference.get("ref_area_sector_locality")
    ref_state = local_reference.get("ref_state_ut")
    ref_city = local_reference.get("ref_village_town_city")
    ref_pin = local_reference.get("ref_pin_code")
    ref_district = local_reference.get("ref_district")

    ##################################################################################
    record.upc_code = upc_code
    record.upcvalidupto = upcValidUpto
    record.caf_type = caf_type
    record.ref_otp = ref_otp
    record.ref_otp_time = ref_otp_timestamp
    record.pwd=pwd
    record.name = name
    record.f_h_name = father_husband_name
    record.gender = gender
    record.date_of_birth = dob
    record.perm_addr_hno = house
    record.perm_addr_street = landmark
    record.perm_addr_locality = ", ".join(filter(None, [locality, district]))
    record.perm_addr_city = vtc
    record.perm_addr_state = state
    record.perm_addr_pin = pin if pin and pin.isdigit() else None
    record.unq_resp_code_pos = pos_unique_code
    record.unq_resp_code_cust = cst_unique_code
    record.unq_resp_date_pos = pos_res_timestamp
    record.unq_resp_date_cust = cst_res_timestamp
    record.email = email_id
    record.subscriber_type = subscriber_type
    record.circle_code = circle_code
    record.nationality = nationality
    record.other_connection_det = number_of_mobile_connections
    record.alternate_contact_no = customer_alternate_mobile_number
    #record.alternate_contact_no =
    # record.photo_aadhaar = decoded_photo
    # record.photo_pos = decoded_pos_live_photo
    # record.photo = decoded_subscriber_live_photo
    record.photo_id_sno = masked_adhar
    record.device_ip = actual_ip
    record.device_mac = device_mac
    record.app_version = app_version
    record.live_photo_time = timezone.localtime(timezone.now())
    record.pos_adh_name = pos_name_adh
    record.latitude= lat
    record.longitude= lng
    record.local_ref_name = ref_name
    record.local_ref = ref_address 
    record.local_ref_contact = ref_mobile
    record.ref_careof_address= ref_careof
    record.ref_landmark= ref_landmark
    record.ref_district= ref_district
    record.local_addr_hno = ref_house
    record.local_addr_street = ref_street
    record.local_addr_locality = ref_area
    record.local_addr_city = ref_city
    record.local_addr_state = ref_state
    record.local_addr_pin = ref_pin
    record.save()
    
    current_time = datetime.now().isoformat()
    # gsm_obj = GsmChoice.objects.get(gsmno=mobileno)
    # gsm_obj.status = 7
    # gsm_obj.save(update_fields=["status"])
    if connection_type=="postpaid":
        response= create_cafid.update_postpaid_sim(simno,mobileno,caf_type)   
    else:
        response= create_cafid.update_prepaid_sim(simno,mobileno,caf_type)
    
    
    if response["status"] == "error":
        return Response({
            "status": "error",
            "message": response["message"]
        }, status=400)


    return Response({
        "status": "success",
        "message": "CAF details updated successfully",
        "caf_id":caf_no,
        "mobileno": mobileno,
        "simnumber": simno,
        "category": connection_type,
        "time_act": current_time
    }, status=200)