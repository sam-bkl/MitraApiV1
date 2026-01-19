from rest_framework import serializers
from .models import Esimprepaid
from ..models import CosBcd
import base64
from django.core.validators import RegexValidator
from datetime import datetime


class EsimprepaidSerializer(serializers.ModelSerializer):
    qr_code = serializers.SerializerMethodField()

    class Meta:
        model = Esimprepaid
        fields = [
            "simno",
            "imsi",
            "status",
            "circle_code",
            "changed_date",
            "qr_code",
            "dual_imsi",
        ]

    def get_qr_code(self, obj):
        if obj.qr_code:
            return base64.b64encode(obj.qr_code).decode("utf-8")
        return None
    



class POISerializer(serializers.Serializer):
    """Point of Identity validation"""
    name = serializers.CharField( required=True, max_length=150, error_messages={
        "required":"this is the issue"
    })
    dob = serializers.CharField( required=False, allow_blank=True)
    gender = serializers.CharField( required=False, max_length=24)

    def to_internal_value(self, data):
        """
        Transform @name → name BEFORE validation
        This runs BEFORE any field validation
        """
        # Normalize @ notation to regular names for internal processing
        normalized = {}
        for key, value in (data or {}).items():
            if key.startswith('@'):
                # @name → name
                normalized[key] = value
            else:
                normalized[key] = value
        
        # Call parent to do validation with normalized data
        return super().to_internal_value(normalized)

class POASerializer(serializers.Serializer):
    """Point of Address validation"""
    co = serializers.CharField(source='@co', required=False, max_length=300)
    house = serializers.CharField(source='@house', required=False, max_length=600)
    street = serializers.CharField(source='@street', required=False, max_length=600)
    lm = serializers.CharField(source='@lm', required=False, max_length=300)
    loc = serializers.CharField(source='@loc', required=False, allow_null=True)
    vtc = serializers.CharField(source='@vtc', required=False, max_length=300)
    subdist = serializers.CharField(source='@subdist', required=False, max_length=300)
    dist = serializers.CharField(source='@dist', required=False, max_length=150)
    state = serializers.CharField(source='@state', required=False, max_length=150)
    pc = serializers.CharField(source='@pc', required=False, max_length=10)

    def to_internal_value(self, data):
        """
        Transform @name → name BEFORE validation
        This runs BEFORE any field validation
        """
        # Normalize @ notation to regular names for internal processing
        normalized = {}
        for key, value in (data or {}).items():
            if key.startswith('@'):
                # @name → name
                normalized[key] = value
            else:
                normalized[key] = value
        
        # Call parent to do validation with normalized data
        return super().to_internal_value(normalized)

class MNPDetailsSerializer(serializers.Serializer):
    """MNP specific details"""
    upc = serializers.CharField(required=False, allow_blank=True, max_length=30)
    upcValidUptoDate = serializers.DateTimeField(required=False)
    mnpConnectionType = serializers.CharField(required=False, max_length=20)

class LocalReferenceSerializer(serializers.Serializer):
    """Local reference details for outstation"""
    ref_name = serializers.CharField(required=False, max_length=150)
    ref_mobile_number = serializers.CharField(required=False, max_length=20)
    ref_address = serializers.CharField(required=False, max_length=750)
    ref_otp = serializers.CharField(required=False, max_length=10)
    ref_otp_timestamp = serializers.DateTimeField(required=False)
    ref_careof_address = serializers.CharField(required=False, max_length=200)
    ref_house_name_no = serializers.CharField(required=False, max_length=600)
    ref_street_address = serializers.CharField(required=False, max_length=600)
    ref_landmark = serializers.CharField(required=False, max_length=200)
    ref_area_sector_locality = serializers.CharField(required=False, max_length=600)
    ref_state_ut = serializers.CharField(required=False, max_length=90)
    ref_village_town_city = serializers.CharField(required=False, max_length=150)
    ref_pin_code = serializers.CharField(required=False, max_length=10)
    ref_district = serializers.CharField(required=False, max_length=150)

class PostpaidPlanSerializer(serializers.Serializer):
    """Postpaid plan details"""
    plan_name = serializers.CharField(required=False, max_length=200)
    plan_code = serializers.CharField(required=False, max_length=50)

class PostpaidDetailsSerializer(serializers.Serializer):
    """Postpaid connection details"""
    stdIsd = serializers.CharField(required=False, max_length=10)
    deposit = serializers.CharField(required=False, max_length=5)
    reasonForNoDeposit = serializers.CharField(required=False, max_length=100)
    methodOfPayment = serializers.CharField(required=False, max_length=50)
    amountReceived = serializers.CharField(required=False, max_length=20)
    plan = PostpaidPlanSerializer(required=False)

class FRCPlanSerializer(serializers.Serializer):
    """FRC plan details for prepaid"""
    plan_name = serializers.CharField(required=False, max_length=200)
    plan_code = serializers.CharField(required=False, max_length=50)
    category_code = serializers.CharField(required=False, max_length=50)

class FRCDetailsSerializer(serializers.Serializer):
    """FRC details for prepaid"""
    frc_plan_prepaid = FRCPlanSerializer(required=False)
    frc_ctopup_number = serializers.CharField(required=False, max_length=50)
    frc_ctopup_number_mpin = serializers.CharField(required=False, max_length=10)

class LocationSerializer(serializers.Serializer):
    """GPS location"""
    lat = serializers.CharField(required=False, max_length=50)
    lng = serializers.CharField(required=False, max_length=50)

class UpdateCAFDetailsSerializer(serializers.Serializer):
    """Main CAF update serializer with validation"""
    
    # Required fields
    customer_aadhaar = serializers.CharField(max_length=12, required=True)
    circle_code = serializers.CharField(max_length=10, required=True)
    ctopup_number = serializers.CharField(max_length=50, required=True)
    ssa_code = serializers.CharField(max_length=30, required=True)
    mobileno = serializers.CharField(max_length=30, required=True)
    simno = serializers.CharField(max_length=150, required=False,allow_blank=True)
    connection_type = serializers.ChoiceField(choices=['prepaid', 'postpaid'], required=True)
    caf_type = serializers.ChoiceField(choices=['cymn', 'mnp', 'simswap', 'simupgrade'], required=True)
    customer_type = serializers.CharField(max_length=30, required=False) 
    
    # Auth fields
    ctopup_username = serializers.CharField(max_length=150, required=False, allow_blank=True)
    pwd = serializers.CharField(max_length=9, required=True)
    vendorcode = serializers.CharField(max_length=150, required=True)
    
    # Subscriber info
    Poi = serializers.JSONField( required=True )
    posPoi = serializers.JSONField( required=True)
    Poa = serializers.JSONField( required=True)
    father_husband_name = serializers.CharField(max_length=300, required=False)
    subscriber_type = serializers.CharField(max_length=50, required=False)
    profession = serializers.CharField(max_length=60, required=False, allow_blank=True)
    nationality = serializers.CharField(max_length=60, required=False)
    
    # Documents
    Pht = serializers.CharField(required=True)  # base64 Aadhaar photo
    posPht = serializers.CharField(required=True)  # base64 POS Aadhaar photo
    subscriber_live_photo = serializers.CharField(required=True)  # base64 live photo
    pwd_certificate = serializers.CharField(required=False, allow_blank=True)
    pos_aadhaar  = serializers.CharField(required=False, allow_blank=True)
    masked_adhar = serializers.CharField(max_length=75, required=False)
    
    # Unique response codes
    cst_unique_code = serializers.CharField(max_length=60, required=False)
    cst_res_timestamp = serializers.DateTimeField(required=False)
    posUid = serializers.DictField(required=False)
    posPoa = serializers.DictField(required=False)
    pos_unique_code = serializers.CharField(max_length=60, required=False)
    pos_res_timestamp = serializers.DateTimeField(required=False)
    
    # Contact details
    email_id = serializers.EmailField(required=False, allow_blank=True)
    number_of_mobile_connections = serializers.CharField(max_length=450, required=False)
    customer_alternate_mobile_number = serializers.CharField(max_length=20, required=False)
    
    # Device info
    device_mac = serializers.CharField(max_length=50, required=False)
    app_version = serializers.CharField(max_length=10, required=True)
    current_location = LocationSerializer(required=False)
    
    # MNP & Special
    mnp_details = MNPDetailsSerializer(required=False)
    outstation_reference = LocalReferenceSerializer(required=False)
    
    # Connection-specific
    postpaid_details = PostpaidDetailsSerializer(required=False)
    frc_details = FRCDetailsSerializer(required=False)
    
    # PWD
    pwd_per_disability = serializers.CharField(required=False, allow_blank=True)

    def validate_connection_type(self, value):
        """Validate connection type"""
        if value not in ['prepaid', 'postpaid']:
            raise serializers.ValidationError(
                f"Connection type must be 'prepaid' or 'postpaid', got '{value}'"
            )
        return value

    def validate_caf_type(self, value):
        """Validate CAF type"""
        valid_types = ['cymn', 'mnp', 'simswap', 'simupgrade']
        if value not in valid_types:
            raise serializers.ValidationError(
                f"CAF type must be one of {valid_types}, got '{value}'"
            )
        return value

    def validate_app_version(self, value):
        """Validate app version"""
        allowed_versions = {'1.1.0'}
        if value not in allowed_versions:
            raise serializers.ValidationError(
                f"Unsupported app version: {value}. Update required."
            )
        return value

    # def validate_mobileno(self, value):
    #     """Validate mobile number format"""
    #     if not value.isdigit() or len(value) != 10:
    #         raise serializers.ValidationError(
    #             "Mobile number must be exactly 10 digits"
    #         )
    #     return value

    # def validate_Poi(self, value):
    #     """Validate POI data"""
    #     if 'name' not in value or not value['name'].strip():
    #         raise serializers.ValidationError("Name is required in POI")
    #     return value

    # def validate_Poa(self, value):
    #     """Validate POA data"""
    #     required_fields = ['state']
    #     for field in required_fields:
    #         if field not in value or not value[field]:
    #             raise serializers.ValidationError(
    #                 f"Field {field} is required in POA"
    #             )
    #     return value