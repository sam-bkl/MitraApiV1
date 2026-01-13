from rest_framework import serializers
from .dkyc_models import CosBcdDkyc

CONNECTION_TYPE_MAP = {
    "postpaid": 1,
    "prepaid": 2,
}


class CosBcdDkycCreateSerializer(serializers.ModelSerializer):

    # =========================
    # Vendor / Dealer
    # =========================
    dkyc_vendor_code = serializers.CharField(source='de_csccode', required=True)
    dkyc_ctopup_username = serializers.CharField(source='de_username', required=True)
    dkyc_circle_code = serializers.CharField(source='circle_code', required=True)
    dkyc_user_ssa_code = serializers.CharField(source='ssa_code', required=False, allow_blank=True, allow_null=True)
    dkyc_caf_no = serializers.CharField(source='caf_serial_no', required=False, allow_blank=True, allow_null=True)
    dkyc_caf_type = serializers.CharField(source='caf_type', required=False, allow_blank=True, allow_null=True)
    # =========================
    # Connection
    # =========================
    dkyc_type_of_connection = serializers.CharField(write_only=True,required=True)
    dkyc_sim_type = serializers.CharField(source='sim_type', required=False, allow_blank=True, allow_null=True)
    dkyc_7_subscriber_status = serializers.CharField(source='subscriber_type', required=True)
    dkyc_8_nationality = serializers.CharField(source='nationality', required=False, allow_blank=True, allow_null=True)

    # =========================
    # SIM / GSM / OTP
    # =========================
    dkyc_selected_mobile_number = serializers.CharField(source='gsmnumber', required=False, allow_blank=True, allow_null=True)
    dkyc_22_sim_no = serializers.CharField(source='sim_no', required=True)
    dkyc_21_customer_mobile_no = serializers.CharField(source='cust_mob_no', required=True)
    dkyc_21_customer_otp = serializers.CharField(source='customer_otp', required=True)
    dkyc_21_customer_otp_time = serializers.DateTimeField(source='customer_otp_time', required=True)
    dkyc_21_cutomer_otp_relation = serializers.CharField(
        source='customer_otp_relation', required=False, allow_blank=True, allow_null=True
    )

    # =========================
    # Subscriber
    # =========================
    dkyc_12_tariff_plan = serializers.CharField(source='tariff_plan', required=False, allow_blank=True, allow_null=True)
    dkyc_parent_ctopup_number = serializers.CharField(source='parent_ctopup_number', required=False, allow_blank=True, allow_null=True)
    dkyc_mpin = serializers.CharField(source='mpin', required=False, allow_blank=True, allow_null=True)
    dkyc_1_subscriber_name = serializers.CharField(source='subscriber_name', required=True)
    dkyc_1A_pwd_status = serializers.CharField(source='pwd_status', required=False, allow_blank=True, allow_null=True)
    dkyc_2_father_husband_name = serializers.CharField(source='father_husband_name', required=False, allow_blank=True, allow_null=True)
    dkyc_3_gender = serializers.CharField(source='gender', required=False, allow_blank=True, allow_null=True)
    dkyc_4_date_of_birth = serializers.DateField(source='date_of_birth', required=False, allow_null=True)
    dkyc_20_std_isd = serializers.CharField(source='std_isd', required=False, allow_blank=True, allow_null=True)
    dkyc_20_deposit_required = serializers.CharField(source='deposit_required', required=False, allow_blank=True, allow_null=True)
    dkyc_20_no_deposit_reson = serializers.CharField(source='no_deposit_reason', required=False, allow_blank=True, allow_null=True)
    dkyc_20_amount_recieved = serializers.CharField(source='amount_received', required=False, allow_blank=True, allow_null=True)
    dkyc_20_payment_method = serializers.CharField(source='payment_method', required=False, allow_blank=True, allow_null=True)
    dkyc_20_postpaid_plan_name = serializers.CharField(source='postpaid_plan_name', required=False, allow_blank=True, allow_null=True)

    dkyc_20_bank_account_no = serializers.CharField(source='bank_account_no', required=False, allow_blank=True, allow_null=True)
    dkyc_20_ifsc_code = serializers.CharField(source='ifsc_code', required=False, allow_blank=True, allow_null=True)
    dkyc_20_bank_name = serializers.CharField(source='bank_name', required=False, allow_blank=True, allow_null=True)
    dkyc_20_bank_branch = serializers.CharField(source='bank_branch', required=False, allow_blank=True, allow_null=True)
    # =========================
    # Operator Counts
    # =========================
    dkyc_11_jio_count = serializers.CharField(source='jio_count', required=False, allow_null=True)
    dkyc_11_airtel_count = serializers.CharField(source='airtel_count', required=False, allow_null=True)
    dkyc_11_vi_count = serializers.CharField(source='vi_count', required=False, allow_null=True)
    dkyc_11_bsnl_count = serializers.CharField(source='bsnl_count', required=False, allow_null=True)
    dkyc_11_other_count = serializers.CharField(source='other_count', required=False, allow_null=True)

    # =========================
    # Correspondence Address (5*)
    # =========================
    dkyc_5A_relation_type = serializers.CharField(source='corr_relation_type', required=False, allow_blank=True, allow_null=True)
    dkyc_5B_relation_name = serializers.CharField(source='corr_relation_name', required=False, allow_blank=True, allow_null=True)
    dkyc_5C_house_details = serializers.CharField(source='corr_house_details', required=False, allow_blank=True, allow_null=True)
    dkyc_5D_street_address = serializers.CharField(source='corr_street_address', required=False, allow_blank=True, allow_null=True)
    dkyc_5E_landmark = serializers.CharField(source='corr_landmark', required=False, allow_blank=True, allow_null=True)
    dkyc_5F_area_locality = serializers.CharField(source='corr_area_locality', required=False, allow_blank=True, allow_null=True)
    dkyc_5G_city = serializers.CharField(source='corr_city', required=False, allow_blank=True, allow_null=True)
    dkyc_5H_district = serializers.CharField(source='corr_district', required=False, allow_blank=True, allow_null=True)
    dkyc_5I_state_ut = serializers.CharField(source='corr_state_ut', required=False, allow_blank=True, allow_null=True)
    dkyc_5J_pin_code = serializers.CharField(source='corr_pin_code', required=False, allow_blank=True, allow_null=True)

    # =========================
    # Permanent Address (6*)
    # =========================
    dkyc_6A_relation_type = serializers.CharField(source='perm_relation_type', required=False, allow_blank=True, allow_null=True)
    dkyc_6B_relation_name = serializers.CharField(source='perm_relation_name', required=False, allow_blank=True, allow_null=True)
    dkyc_6C_house_details = serializers.CharField(source='perm_house_details', required=False, allow_blank=True, allow_null=True)
    dkyc_6D_street_address = serializers.CharField(source='perm_street_address', required=False, allow_blank=True, allow_null=True)
    dkyc_6E_landmark = serializers.CharField(source='perm_landmark', required=False, allow_blank=True, allow_null=True)
    dkyc_6F_area_locality = serializers.CharField(source='perm_area_locality', required=False, allow_blank=True, allow_null=True)
    dkyc_6G_city = serializers.CharField(source='perm_city', required=False, allow_blank=True, allow_null=True)
    dkyc_6H_district = serializers.CharField(source='perm_district', required=False, allow_blank=True, allow_null=True)
    dkyc_6I_state_ut = serializers.CharField(source='perm_state_ut', required=False, allow_blank=True, allow_null=True)
    dkyc_6J_pin_code = serializers.CharField(source='perm_pin_code', required=False, allow_blank=True, allow_null=True)

    # =========================
    # Additional Information
    # =========================
    dkyc_13_value_added_services = serializers.CharField(source='value_added_services', required=False, allow_blank=True, allow_null=True)
    dkyc_14_email_address = serializers.CharField(source='email_address', required=False, allow_blank=True, allow_null=True)
    dkyc_16_profession = serializers.CharField(source='profession', required=False, allow_blank=True, allow_null=True)
    dkyc_17_pan_gir = serializers.CharField(source='pan_gir', required=False, allow_blank=True, allow_null=True)

    dkyc_18_alt_home_number = serializers.CharField(source='alt_home_number', required=False, allow_blank=True, allow_null=True)
    dkyc_18_alt_business_number = serializers.CharField(source='alt_business_number', required=False, allow_blank=True, allow_null=True)
    dkyc_18_alt_mobile_number = serializers.CharField(source='alt_mobile_number', required=False, allow_blank=True, allow_null=True)

    # =========================
    # POI / POA
    # =========================
    dkyc_9_poi_type = serializers.CharField(source='poi_type', required=False, allow_blank=True, allow_null=True)
    dkyc_9_poi_number = serializers.CharField(source='poi_number', required=False, allow_blank=True, allow_null=True)
    dkyc_9_poi_date_of_issue = serializers.DateField(source='poi_date_of_issue', required=False, allow_null=True)
    dkyc_9_poi_place_of_issue = serializers.CharField(source='poi_place_of_issue', required=False, allow_blank=True, allow_null=True)
    dkyc_9_poi_issue_authority = serializers.CharField(source='poi_issue_authority', required=False, allow_blank=True, allow_null=True)

    dkyc_10_poa_type = serializers.CharField(source='poa_type', required=False, allow_blank=True, allow_null=True)
    dkyc_10_poa_number = serializers.CharField(source='poa_number', required=False, allow_blank=True, allow_null=True)
    dkyc_10_poa_date_of_issue = serializers.DateField(source='poa_date_of_issue', required=False, allow_null=True)
    dkyc_10_poa_place_of_issue = serializers.CharField(source='poa_place_of_issue', required=False, allow_blank=True, allow_null=True)
    dkyc_10_poa_issue_authority = serializers.CharField(source='poa_issue_authority', required=False, allow_blank=True, allow_null=True)

    # =========================
    # POS OTP & Location
    # =========================
    dkyc_pos_otp = serializers.CharField(source='pos_otp', required=False, allow_blank=True, allow_null=True)
    dkyc_pos_otp_generated_time = serializers.DateTimeField(source='pos_otp_gen_time', required=False, allow_null=True)
    dkyc_pos_otp_ver_time = serializers.DateTimeField(source='pos_otp_ver_time', required=False, allow_null=True)
    dkyc_pos_latitude = serializers.CharField(source='pos_lat', required=False, allow_blank=True, allow_null=True)
    dkyc_pos_longitude = serializers.CharField(source='pos_lang', required=False, allow_blank=True, allow_null=True)
    dkyc_cust_latitude = serializers.CharField(source='cust_lat', required=False, allow_blank=True, allow_null=True)
    dkyc_cust_longitude = serializers.CharField(source='cust_lang', required=False, allow_blank=True, allow_null=True)
    dkyc_pos_declaration_check = serializers.BooleanField(source='pos_declaration_check', required=False, allow_null=True)
    # =========================
    # UPC / Outstation
    # =========================
    dkyc_19_upc_code = serializers.CharField(source='upc_code', required=False, allow_blank=True, allow_null=True)
    dkyc_19_upc_validity = serializers.DateTimeField(
    source='upcvalidupto',
    required=False,
    allow_null=True
)
    dkyc_19_previous_operator = serializers.CharField(source='prev_optr', required=False, allow_blank=True, allow_null=True)

    dkyc_18_outstation_reference_name = serializers.CharField(source='outstation_ref_name', required=False, allow_blank=True, allow_null=True)
    dkyc_18_outstation_reference_phone = serializers.CharField(source='outstation_mob_no', required=False, allow_blank=True, allow_null=True)
    dkyc_18_outstation_house_address = serializers.CharField(source='outstation_address', required=False, allow_blank=True, allow_null=True)
    dkyc_29_outstation_otp_ver_time = serializers.DateTimeField(source='outstation_otp_ver_time', required=False, allow_null=True)
    dkyc_29_outstation_otp_code = serializers.CharField(source='outstation_otp_code', required=False, allow_blank=True, allow_null=True)
    dkyc_29_outstation_otp_gen_time = serializers.DateTimeField(source='outstation_otp_gen_time', required=False, allow_null=True)
    dkyc_pwd_per_disability = serializers.CharField(source='pwd_per_disability', required=False, allow_blank=True, allow_null=True)
    dkyc_type_disability= serializers.CharField(source='type_disability', required=False, allow_blank=True, allow_null=True)
    # =========================
    # Images (Base64)
    # =========================
    dkyc_poiDocumentFront = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
    dkyc_poiDocumentBack = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
    dkyc_poaDocumentFront = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
    dkyc_poaDocumentBack = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
    dkyc_customerPhoto = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
    dkyc_posPhoto = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
    dkyc_pwd_doc_photo = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
    dkyc_app_version = serializers.CharField(source='app_version', required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = CosBcdDkyc
        fields = "__all__"
        read_only_fields = ("id", "created_at")
    
    def create(self, validated_data):
        validated_data.pop("dkyc_type_of_connection", None)
        for key in [
            "dkyc_poiDocumentFront",
            "dkyc_poiDocumentBack",
            "dkyc_poaDocumentFront",
            "dkyc_poaDocumentBack",
            "dkyc_customerPhoto",
            "dkyc_posPhoto",
            "dkyc_pwd_doc_photo"
        ]:
            validated_data.pop(key, None)

        return CosBcdDkyc.objects.create(**validated_data)
    
    def to_internal_value(self, data):
        data = data.copy()

        if data.get("dkyc_19_upc_validity") in ("", "null", "NULL"):
            data["dkyc_19_upc_validity"] = None
        if data.get("dkyc_9_poi_date_of_issue") in ("", "null", "NULL"):
            data["dkyc_9_poi_date_of_issue"] = None
        if data.get("dkyc_10_poa_date_of_issue") in ("", "null", "NULL"):
            data["dkyc_10_poa_date_of_issue"] = None
        if data.get("dkyc_29_outstation_otp_ver_time") in ("", "null", "NULL"):
            data["dkyc_29_outstation_otp_ver_time"] = None
        if data.get("dkyc_29_outstation_otp_gen_time") in ("", "null", "NULL"):
            data["dkyc_29_outstation_otp_gen_time"] = None
        

        return super().to_internal_value(data)
    
    def validate(self, attrs):
        conn_type_str = self.initial_data.get("dkyc_type_of_connection")

        if not conn_type_str:
            raise serializers.ValidationError({
                "dkyc_type_of_connection": "This field is required."
            })

        conn_type_str = conn_type_str.lower().strip()

        if conn_type_str not in ("postpaid", "prepaid"):
            raise serializers.ValidationError({
                "dkyc_type_of_connection": "Must be 'postpaid' or 'prepaid'."
            })

        # Map string → integer
        attrs["connection_type"] = 2 if conn_type_str == "postpaid" else 1

        return attrs