import base64
import os
from datetime import datetime
from io import BytesIO

from django.db import transaction, DatabaseError
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Esimprepaid,EsimprepaidSold
from ..models import CosBcd, Simprepaid, Simpostpaid
from .serializers import UpdateCAFDetailsSerializer
from ..helper_functions import check_gsm_caf_logic
from ..utils import is_sim_allotted_today, insert_sim_allotment
from ..helperviews.simswap import simswap_save
from .. import create_cafid
from ..inventory_movement.inv_update import update_inventory_atomic


def extract_client_ip(request):
    """Extract actual client IP from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    x_real_ip = request.META.get('HTTP_X_REAL_IP')
    remote_addr = request.META.get('REMOTE_ADDR')

    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    elif x_real_ip:
        return x_real_ip
    return remote_addr


def decode_base64_image(base64_str, field_name):
    """Decode and validate base64 image"""
    if not base64_str:
        raise ValidationError(f"{field_name} is required")
    
    try:
        decoded = base64.b64decode(base64_str)
        if not decoded:
            raise ValidationError(f"Invalid {field_name}")
        return decoded
    except Exception as e:
        raise ValidationError(f"Invalid base64 {field_name}: {str(e)}")


def save_images_to_disk(caf_no, images_dict):
    """
    Save all images to disk atomically
    
    Args:
        caf_no: CAF number
        images_dict: {filename: decoded_bytes, ...}
    
    Returns:
        saved_paths: {filename: full_path, ...}
    """
    today = datetime.now()
    year = today.strftime("%Y")
    month = today.strftime("%m")
    day = today.strftime("%d")

    base_dir = "/cosdata/files/cos_images/"
    full_dir = os.path.join(base_dir, year, month, day)

    os.makedirs(full_dir, exist_ok=True)

    saved_paths = {}
    try:
        for filename, decoded_bytes in images_dict.items():
            filepath = os.path.join(full_dir, filename)
            with open(filepath, "wb") as f:
                f.write(decoded_bytes)
            saved_paths[filename] = filepath
        return saved_paths
    except IOError as e:
        raise ValidationError(f"Failed to save images: {str(e)}")


def extract_poi_data(poi_dict):
    """Extract POI (Point of Identity) data"""
    return {
        'name': poi_dict.get('@name'),
        'dob': poi_dict.get('@dob'),
        'gender': poi_dict.get('@gender'),
    }


def extract_poa_data(poa_dict):
    """Extract POA (Point of Address) data"""
    return {
        'f_h_name': poa_dict.get('@co'),
        'house': poa_dict.get('@house'),
        'street': poa_dict.get('@street'),
        'landmark': poa_dict.get('@lm'),
        'locality': poa_dict.get('@loc'),
        'vtc': poa_dict.get('@vtc'),
        'subdistrict': poa_dict.get('@subdist'),
        'district': poa_dict.get('@dist'),
        'state': poa_dict.get('@state'),
        'pin': poa_dict.get('@pc'),
    }


def parse_dob(dob_str):
    """Parse date of birth string"""
    if not dob_str:
        return None
    try:
        return datetime.strptime(dob_str, "%d-%m-%Y")
    except (ValueError, TypeError):
        return None


class CosBcdBuilder:
    """Builder pattern for CosBcd record creation - elegant field assignment"""
    
    def __init__(self, caf_no):
        self.record = CosBcd(caf_serial_no=caf_no)
        self.field_map = {}

    def add_fields(self, **kwargs):
        """Dynamically add fields via kwargs"""
        for key, value in kwargs.items():
            if value is not None:
                setattr(self.record, key, value)
        return self

    def add_conditional_field(self, field_name, value, condition=True):
        """Add field only if condition is True"""
        if condition and value is not None:
            setattr(self.record, field_name, value)
        return self

    def add_joined_field(self, field_name, *parts):
        """Join multiple parts with ', ' and set field"""
        joined = ", ".join(filter(None, parts))
        if joined:
            setattr(self.record, field_name, joined)
        return self

    def add_from_dict(self, field_mapping, source_dict):
        """
        Bulk add fields from dictionary using field mapping
        
        Args:
            field_mapping: {model_field: source_key, ...}
            source_dict: source data dictionary
        """
        for model_field, source_key in field_mapping.items():
            value = source_dict.get(source_key)
            if value is not None:
                setattr(self.record, model_field, value)
        return self

    def build(self):
        """Return the built record"""
        return self.record


def determine_sim_type(simno, connection_type):
    """
    Determine SIM type (USIM or regular)
    
    Returns:
        2 = USIM (product_code 7003, 7004)
        1 = Regular SIM
    """
    if connection_type == 1:  # prepaid
        sim = Simprepaid.objects.filter(simno=simno).values('product_code').first()
    else:  # postpaid
        sim = Simpostpaid.objects.filter(simno=simno).values('product_code').first()

    if sim and sim['product_code'] in (7003, 7004):
        return 2
    return 1

def reserve_esim(circle_code):
    """
    Atomically reserve ONE available eSIM.
    Safe against parallel requests.
    """

    esim = (
        Esimprepaid.objects
        .select_for_update(skip_locked=True)
        .filter(status=1, circle_code=circle_code)
        .order_by("simno")   # deterministic selection
        .first()
    )

    if not esim:
        raise ValidationError("No eSIM available for allocation")

    esim.status = 2  # Reserved
    esim.changed_date = timezone.now()
    esim.save(update_fields=["status", "changed_date"])

    return esim


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_caf_details(request):
    """
    Update CAF (Customer Application Form) details
    
    Fully atomic transaction with proper error handling and validation
    No partial updates - all or nothing
    """
    
    # =====================================================
    # 1️⃣ VALIDATION & DESERIALIZATION
    # =====================================================
    serializer = UpdateCAFDetailsSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {
                "status": "error",
                "message": "Validation failed",
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    data = serializer.validated_data

    # =====================================================
    # 2️⃣ PRE-TRANSACTION CHECKS
    # =====================================================
    
    # Extract client IP
    actual_ip = extract_client_ip(request)

    # Check GSM-CAF logic
    result = check_gsm_caf_logic(data['mobileno'], data['caf_type'])
    if result.get("Allow") == "No":
        return Response(
            {"status": "error", "message": result.get("Reason")},
            status=status.HTTP_403_FORBIDDEN
        )

    # Check SIM allotment restriction
    customer_aadhaar = data['customer_aadhaar']
    circle_code = data['circle_code']
    
    exists, previous_gsm = is_sim_allotted_today(customer_aadhaar, circle_code)
    if exists:
        verified_flag = (
            CosBcd.objects
            .filter(gsmnumber=previous_gsm)
            .values_list("verified_flag", flat=True)
            .first()
        )
        if verified_flag != "R":
            return Response({
                "status": "failed",
                "message": "SIM already allotted within restriction window",
                "previous_gsm": previous_gsm
            }, status=status.HTTP_400_BAD_REQUEST)

    # =====================================================
    # 3️⃣ DECODE & VALIDATE IMAGES
    # =====================================================
    try:
        decoded_photo = decode_base64_image(data.get('Pht'), "Aadhaar photo")
        decoded_live_photo = decode_base64_image(data.get('subscriber_live_photo'), "Live photo")
        decoded_pos_ad_photo = decode_base64_image(data.get('posPht'), "POS Aadhaar photo")
        
        decoded_pwd_cert = None
        if data.get('pwd_certificate'):
            decoded_pwd_cert = decode_base64_image(data.get('pwd_certificate'), "PWD Certificate")
    
    except ValidationError as e:
        return Response(
            {"status": "error", "message": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

    # =====================================================
    # 4️⃣ ATOMIC TRANSACTION BLOCK
    # =====================================================
    try:
        with transaction.atomic():
            
            # Generate CAF ID
            caf_no = create_cafid.get_caf_id()
            if not caf_no:
                raise ValidationError("Failed to generate CAF ID")

            # Save images to disk
            images_dict = {
                f"{caf_no}a.jpg": decoded_photo,
                f"{caf_no}l.jpg": decoded_live_photo,
                f"{caf_no}pa.jpg": decoded_pos_ad_photo,
            }
            if decoded_pwd_cert:
                images_dict[f"{caf_no}pwd.jpg"] = decoded_pwd_cert
            
            saved_paths = save_images_to_disk(caf_no, images_dict)

            # Handle SIMSWAP special case
            simstate = circle_code
            if data['caf_type'] == 'simswap':
                simswap_result = simswap_save(
                    request, caf_no, data['ctopup_number'], 
                    actual_ip, data['mobileno']
                )
                if simswap_result.get("status") != "success":
                    raise ValidationError(simswap_result.get("message", "SIMSWAP failed"))
                simstate = simswap_result.get("circle_code_cust", circle_code)

            # Parse data
            poi_data = extract_poi_data(data.get('Poi', {}))
            poa_data = extract_poa_data(data.get('Poa', {}))
            local_ref = data.get('outstation_reference', {})
            postpaid_details = data.get('postpaid_details', {})
            frc_details = data.get('frc_details', {})
            mnp_details = data.get('mnp_details', {})
            current_location = data.get('current_location', {})

            # Determine connection type code
            connection_type_code = 2 if data['connection_type'] == 'postpaid' else 1

            # Determine SIM type
            sim_type = determine_sim_type(data['simno'], connection_type_code)

            # Create CosBcd record using builder pattern
            builder = CosBcdBuilder(caf_no)
            
            # Basic fields
            builder.add_fields(
                de_csccode=data.get('vendorcode'),
                de_username=data.get('ctopup_username') or data.get('ctopup_number'),
                parent_ctopup_number=data.get('ctopup_number'),
                gsmnumber=data['mobileno'],
                simnumber=data['simno'],
                ssa_code=data.get('ssa_code'),
                simstate=simstate,
                connection_type=connection_type_code,
                caf_type=data['caf_type'],
                circle_code=circle_code,
                sim_type=sim_type,
                pwd=data.get('pwd'),
                pwd_per_disability=data.get('pwd_per_disability'),
                app_version=data.get('app_version'),
                device_ip=actual_ip,
                device_mac=data.get('device_mac'),
                live_photo_time=timezone.now()
            )
            
            # POI (Point of Identity) data
            builder.add_fields(
                name=poi_data.get('name'),
                gender=poi_data.get('gender')
            ).add_conditional_field(
                'date_of_birth',
                parse_dob(poi_data.get('dob')),
                poi_data.get('dob') is not None
            )
            
            # POA (Point of Address) data
            builder.add_fields(
                father_name_adh=poa_data.get('f_h_name'),
                perm_addr_hno=poa_data.get('house'),
                perm_addr_state=poa_data.get('state')
            ).add_joined_field(
                'perm_addr_street',
                poa_data.get('street'),
                poa_data.get('landmark')
            ).add_joined_field(
                'perm_addr_locality',
                poa_data.get('locality'),
                poa_data.get('vtc')
            ).add_joined_field(
                'perm_addr_city',
                poa_data.get('subdistrict'),
                poa_data.get('district')
            )
            
            # Handle PIN as integer
            pin = poa_data.get('pin')
            if pin and pin.isdigit():
                builder.add_fields(perm_addr_pin=int(pin))
            
            # Subscriber details
            builder.add_fields(
                f_h_name=data.get('father_husband_name'),
                profession=data.get('profession'),
                nationality=data.get('nationality'),
                subscriber_type=data.get('subscriber_type'),
                email=data.get('email_id'),
                other_connection_det=data.get('number_of_mobile_connections'),
                alternate_contact_no=data.get('customer_alternate_mobile_number'),
                photo_id_sno=data.get('masked_adhar')
            )
            
            # Location data
            builder.add_fields(
                latitude=current_location.get('lat'),
                longitude=current_location.get('lng')
            )
            
            # Response codes
            builder.add_fields(
                unq_resp_code_cust=data.get('cst_unique_code'),
                unq_resp_code_pos=data.get('pos_unique_code'),
                unq_resp_date_cust=data.get('cst_res_timestamp'),
                unq_resp_date_pos=data.get('pos_res_timestamp')
            )
            
            # MNP details
            builder.add_fields(
                upc_code=mnp_details.get('upc'),
                upcvalidupto=mnp_details.get('upcValidUptoDate')
            )
            if data['caf_type'] == 'mnp':
                mnp_conn_type = mnp_details.get('mnpConnectionType', 'prepaid')
                builder.add_fields(
                    mnp_connection_type=2 if mnp_conn_type == 'postpaid' else 1
                )
            
            # POS details
            pos_poi = data.get('posPoi', {})
            builder.add_fields(pos_adh_name=pos_poi.get('@name'))
            
            # Local reference (outstation)
            local_ref_mapping = {
                'local_ref_name': 'ref_name',
                'local_ref': 'ref_address',
                'local_ref_contact': 'ref_mobile_number',
                'ref_otp': 'ref_otp',
                'ref_otp_time': 'ref_otp_timestamp',
                'ref_careof_address': 'ref_careof_address',
                'local_addr_hno': 'ref_house_name_no',
                'local_addr_street': 'ref_street_address',
                'ref_landmark': 'ref_landmark',
                'local_addr_locality': 'ref_area_sector_locality',
                'local_addr_city': 'ref_village_town_city',
                'local_addr_state': 'ref_state_ut',
                'local_addr_pin': 'ref_pin_code',
                'ref_district': 'ref_district'
            }
            builder.add_from_dict(local_ref_mapping, local_ref)
            
            # Connection-specific fields
            if data['connection_type'] == 'postpaid':
                plan = postpaid_details.get('plan', {})
                builder.add_fields(
                    std_isd=postpaid_details.get('stdIsd'),
                    deposit_required=postpaid_details.get('deposit'),
                    no_deposit_reason=postpaid_details.get('reasonForNoDeposit'),
                    postpaid_plan_name=plan.get('plan_name'),
                    payment_method=postpaid_details.get('methodOfPayment'),
                    amount_received=postpaid_details.get('amountReceived')
                )
            else:  # prepaid
                frc_plan = frc_details.get('frc_plan_prepaid', {})
                builder.add_fields(
                    frc_plan_name=frc_plan.get('plan_name'),
                    frc_plan_code=frc_plan.get('plan_code'),
                    frc_category_code=frc_plan.get('category_code'),
                    frc_ctopup_number=frc_details.get('frc_ctopup_number'),
                    frc_ctopup_number_mpin=frc_details.get('frc_ctopup_number_mpin')
                )
            
            record = builder.build()

            # SAVE RECORD
            record.save()
            
            # Verify save
            if not CosBcd.objects.filter(caf_serial_no=caf_no).exists():
                raise DatabaseError("CAF insert verification failed")

            # Update inventory (SIM + GSM)
            try:
                update_inventory_atomic(
                    simno=data['simno'],
                    gsmno=data['mobileno'],
                    connection_type=connection_type_code,
                    plan=data['caf_type']
                )
            except ValidationError as inv_error:
                raise ValidationError(f"Inventory update failed: {str(inv_error)}")

            # Record allotment
            insert_sim_allotment(customer_aadhaar, data['mobileno'], circle_code)

    except ValidationError as e:
        return Response(
            {
                "status": "error",
                "message": str(e),
                "type": "validation_error"
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    except DatabaseError as e:
        return Response(
            {
                "status": "error",
                "message": "Database error occurred. Please retry.",
                "type": "database_error"
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        return Response(
            {
                "status": "error",
                "message": "An unexpected error occurred",
                "type": "server_error",
                "detail": str(e) if request.user.is_staff else None
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # =====================================================
    # 5️⃣ SUCCESS RESPONSE
    # =====================================================
    return Response({
        "status": "success",
        "message": "CAF details updated successfully",
        "data": {
            "caf_id": caf_no,
            "mobileno": data['mobileno'],
            "simnumber": data['simno'],
            "connection_type": data['connection_type'],
            "caf_type": data['caf_type'],
            "timestamp": timezone.now().isoformat(),
            "images_saved": bool(saved_paths)
        }
    }, status=status.HTTP_200_OK)