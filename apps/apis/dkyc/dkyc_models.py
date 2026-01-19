from django.db import models


class CosBcdDkyc(models.Model):
    id = models.AutoField(primary_key=True)
    de_csccode = models.CharField(max_length=150, null=True, blank=True)
    de_username = models.CharField(max_length=150, null=True, blank=True)
    circle_code = models.CharField(max_length=20, null=True, blank=True)
    ssa_code = models.CharField(max_length=20, null=True, blank=True)
    caf_type = models.CharField(max_length=20, null=True, blank=True)
    caf_serial_no = models.CharField(max_length=20, null=True, blank=True)
    connection_type = models.CharField(max_length=50, null=True, blank=True)
    sim_type = models.CharField(max_length=20, null=True, blank=True)
    subscriber_type = models.CharField(max_length=50, null=True, blank=True)
    nationality = models.CharField(max_length=60, null=True, blank=True)
    gsmnumber = models.CharField(max_length=20, null=True, blank=True)
    sim_no = models.CharField(max_length=20, null=True, blank=True)
    cust_mob_no = models.CharField(max_length=20, null=True, blank=True)
    customer_otp = models.CharField(max_length=10, null=True, blank=True)
    customer_otp_time = models.DateTimeField(null=True, blank=True)
    customer_otp_relation = models.CharField(max_length=20, null=True, blank=True)
    tariff_plan = models.CharField(max_length=100, null=True, blank=True)
    parent_ctopup_number= models.CharField(max_length=20, null=True, blank=True)
    mpin= models.CharField(max_length=10, null=True, blank=True)
    subscriber_name = models.CharField(max_length=200, null=True, blank=True)
    pwd_status = models.CharField(max_length=10, null=True, blank=True)
    father_husband_name = models.CharField(max_length=200, null=True, blank=True)
    gender = models.CharField(max_length=20, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    jio_count = models.CharField(null=True, blank=True)
    airtel_count = models.CharField(null=True, blank=True)
    vi_count = models.CharField(null=True, blank=True)
    bsnl_count = models.CharField(null=True, blank=True)
    other_count = models.CharField(null=True, blank=True)
    
    # Correspondence Address
    corr_relation_type = models.CharField(max_length=50, null=True, blank=True)
    corr_relation_name = models.CharField(max_length=150, null=True, blank=True)
    corr_house_details = models.CharField(max_length=150, null=True, blank=True)
    corr_street_address = models.CharField(max_length=150, null=True, blank=True)
    corr_landmark = models.CharField(max_length=150, null=True, blank=True)
    corr_area_locality = models.CharField(max_length=150, null=True, blank=True)
    corr_city = models.CharField(max_length=100, null=True, blank=True)
    corr_district = models.CharField(max_length=100, null=True, blank=True)
    corr_state_ut = models.CharField(max_length=100, null=True, blank=True)
    corr_pin_code = models.CharField(max_length=10, null=True, blank=True)
    
    # Permanent Address
    perm_relation_type = models.CharField(max_length=50, null=True, blank=True)
    perm_relation_name = models.CharField(max_length=150, null=True, blank=True)
    perm_house_details = models.CharField(max_length=150, null=True, blank=True)
    perm_street_address = models.CharField(max_length=150, null=True, blank=True)
    perm_landmark = models.CharField(max_length=150, null=True, blank=True)
    perm_area_locality = models.CharField(max_length=150, null=True, blank=True)
    perm_city = models.CharField(max_length=100, null=True, blank=True)
    perm_district = models.CharField(max_length=100, null=True, blank=True)
    perm_state_ut = models.CharField(max_length=100, null=True, blank=True)
    perm_pin_code = models.CharField(max_length=10, null=True, blank=True)
    
    # Additional Information
    value_added_services = models.CharField(max_length=150, null=True, blank=True)
    email_address = models.CharField(max_length=150, null=True, blank=True)
    profession = models.CharField(max_length=100, null=True, blank=True)
    pan_gir = models.CharField(max_length=20, null=True, blank=True)
    alt_home_number = models.CharField(max_length=15, null=True, blank=True)
    alt_business_number = models.CharField(max_length=15, null=True, blank=True)
    alt_mobile_number = models.CharField(max_length=15, null=True, blank=True)
    
    # Proof of Identity
    poi_type = models.CharField(max_length=50, null=True, blank=True)
    poi_number = models.CharField(max_length=50, null=True, blank=True)
    poi_date_of_issue = models.DateField(null=True, blank=True)
    poi_place_of_issue = models.CharField(max_length=100, null=True, blank=True)
    poi_issue_authority = models.CharField(max_length=100, null=True, blank=True)
    
    # Proof of Address
    poa_type = models.CharField(max_length=50, null=True, blank=True)
    poa_number = models.CharField(max_length=50, null=True, blank=True)
    poa_date_of_issue = models.DateField(null=True, blank=True)
    poa_place_of_issue = models.CharField(max_length=100, null=True, blank=True)
    poa_issue_authority = models.CharField(max_length=100, null=True, blank=True)
    
    # Declarations
    pos_declaration_check = models.BooleanField(null=True, blank=True)
    declaration1 = models.BooleanField(null=True, blank=True)
    declaration2 = models.BooleanField(null=True, blank=True)
    declaration3 = models.BooleanField(null=True, blank=True)
    
    # Documents
    poi_document_front = models.CharField(max_length=255, null=True, blank=True)
    poi_document_back = models.CharField(max_length=255, null=True, blank=True)
    poa_document_front = models.CharField(max_length=255, null=True, blank=True)
    poa_document_back = models.CharField(max_length=255, null=True, blank=True)
    customer_photo = models.CharField(max_length=255, null=True, blank=True)
    pos_photo = models.CharField(max_length=255, null=True, blank=True)
    
    # POS OTP
    pos_otp = models.CharField(max_length=10, null=True, blank=True)
    pos_otp_gen_time = models.DateTimeField(null=True, blank=True)
    pos_otp_ver_time = models.DateTimeField(null=True, blank=True)
    
    # Location
    pos_lat = models.CharField(max_length=20, null=True, blank=True)
    pos_lang = models.CharField(max_length=20, null=True, blank=True)
    cust_lat = models.CharField(max_length=20, null=True, blank=True)
    cust_lang = models.CharField(max_length=20, null=True, blank=True)
    
    # UPC and Previous Operator
    upc_code = models.CharField(max_length=30, null=True, blank=True)
    upcvalidupto = models.DateField(null=True, blank=True)
    prev_optr = models.CharField(max_length=60, null=True, blank=True)
    prev_optr_area = models.CharField(max_length=60, null=True, blank=True)
    
    # Payment
    payment_mode = models.CharField(max_length=60, null=True, blank=True)
    std_isd = models.CharField(max_length=10, null=True, blank=True)
    deposit_required = models.CharField(max_length=5, null=True, blank=True)
    no_deposit_reason = models.CharField(max_length=100, null=True, blank=True)
    payment_method = models.CharField(max_length=50, null=True, blank=True)
    amount_received = models.CharField(max_length=50, null=True, blank=True)
    postpaid_plan_name = models.CharField(max_length=50, null=True, blank=True)
    bank_account_no = models.CharField(max_length=50, null=True, blank=True)
    ifsc_code = models.CharField(max_length=20, null=True, blank=True)
    bank_name = models.CharField(max_length=100, null=True, blank=True)
    bank_branch = models.CharField(max_length=100, null=True, blank=True)
    # Outstation Reference
    outstation_ref_name = models.CharField(max_length=200, null=True, blank=True)
    outstation_mob_no = models.CharField(max_length=20, null=True, blank=True)
    outstation_address = models.CharField(max_length=350, null=True, blank=True)
    outstation_otp_code = models.CharField(max_length=10, null=True, blank=True)
    outstation_otp_gen_time = models.DateTimeField(null=True, blank=True)
    outstation_otp_ver_time = models.DateTimeField(null=True, blank=True)
        
    # Device Information
    device_ip = models.CharField(max_length=30, null=True, blank=True)
    device_mac = models.CharField(max_length=50, null=True, blank=True)
    
    # Verification
    verified_flag = models.CharField(max_length=255, null=True, blank=True)
    verified_by = models.CharField(max_length=255, null=True, blank=True)
    verified_date = models.DateTimeField(null=True, blank=True)
    app_version = models.CharField(max_length=10, null=True, blank=True)
    rejection_reason = models.TextField(null=True, blank=True)
    customer_type = models.CharField(max_length=10, null=True, blank=True)
    # PWD details
    type_disability = models.CharField(max_length=100, null=True, blank=True)
    pwd_per_disability = models.CharField(max_length=20, null=True, blank=True)
    pwd_doc_photo = models.CharField(max_length=200, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.CharField(max_length=25, null=True, blank=True)
    auth_per_desig = models.CharField(max_length=50, null=True, blank=True)
    cug_reference_id = models.CharField(max_length=20, null=True, blank=True)
    cug_group_id = models.CharField(max_length=30, null=True, blank=True)
    class Meta:
        managed = False
        app_label= 'apis'
        db_table = 'cos_bcd_dkyc'

    def __str__(self):
        return f"{self.caf_no} - {self.subscriber_name}"
    

class DkycCustSignOtp(models.Model):
    cust_no = models.CharField(max_length=15)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        app_label= 'apis'
        db_table = "dkyc_cust_sign_otp"


class DkycPosSignOtp(models.Model):
    pos_no = models.CharField(max_length=15)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        app_label= 'apis'
        db_table = "dkyc_pos_sign_otp"

class BulkBusinessGroups(models.Model):
    business_group_id = models.AutoField(primary_key=True)
    reference_number = models.CharField(max_length=50)
    business_group_name = models.CharField(max_length=200)
    business_group_type = models.CharField(max_length=20)
    type_of_caf = models.CharField(max_length=20, default='DKYC')
    connection_type = models.CharField(max_length=20)
    business_group_size = models.IntegerField()
    business_group_billing = models.CharField(max_length=100)
    cafs_required = models.CharField(max_length=20, null=True, blank=True)
    scope = models.CharField(max_length=100)
    visibility = models.CharField(max_length=100)
    tv_required = models.CharField(max_length=20, null=True, blank=True)
    status = models.CharField(max_length=30, default='Pending for Approval')
    created_date = models.DateTimeField()
    approved_date = models.DateTimeField(null=True, blank=True)
    approved_by = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    circle_code = models.CharField(max_length=10, null=True, blank=True)
    ssa_code = models.CharField(max_length=30, null=True, blank=True)
    insert_user_id = models.CharField(max_length=30, null=True, blank=True)
    insert_user_name = models.CharField(max_length=100, null=True, blank=True)
    approve_remark = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        managed = False
        app_label= 'apis'
        db_table = "bulk_business_groups"

class CompanyInformations(models.Model):
    company_info_id = models.AutoField(primary_key=True)
    business_group = models.ForeignKey(
        BulkBusinessGroups,
        db_column="business_group_id",
        on_delete=models.DO_NOTHING,
        related_name="companyinformations"
    )
    company_name = models.CharField(max_length=300)
    type_of_organization = models.CharField(max_length=100)
    cin = models.CharField(max_length=50, null=True, blank=True)
    pin = models.CharField(max_length=20, null=True, blank=True)
    registered_address1 = models.CharField(max_length=300)
    registered_address2 = models.CharField(max_length=300, null=True, blank=True)
    registered_address3 = models.CharField(max_length=300, null=True, blank=True)
    registered_pin_code = models.CharField(max_length=10)
    registered_state = models.CharField(max_length=100)
    registered_district = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=20)
    fax = models.CharField(max_length=20, null=True, blank=True)
    email = models.CharField(max_length=100, null=True, blank=True)
    billing_address_same_as_registered = models.BooleanField(default=False)
    billing_address1 = models.CharField(max_length=300, null=True, blank=True)
    billing_address2 = models.CharField(max_length=300, null=True, blank=True)
    billing_address3 = models.CharField(max_length=300, null=True, blank=True)
    billing_pin_code = models.CharField(max_length=10, null=True, blank=True)
    billing_state = models.CharField(max_length=100, null=True, blank=True)
    billing_district = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        app_label= 'apis'
        db_table = "company_informations"
        
class BulkConnectionDetails(models.Model):
    connection_id = models.AutoField(primary_key=True)
    business_group = models.ForeignKey(
        BulkBusinessGroups,
        db_column="business_group_id",
        on_delete=models.DO_NOTHING,
        related_name="connections"
    )
    serial_no = models.IntegerField()
    gsm_number = models.CharField(max_length=20)
    sim_number = models.CharField(max_length=30)
    imsi_number = models.CharField(max_length=30)
    customer_name = models.CharField(max_length=200)
    user_name = models.CharField(max_length=200)
    poi_type = models.CharField(max_length=50)
    poi_number = models.CharField(max_length=100)
    poa_type = models.CharField(max_length=50)
    poa_number = models.CharField(max_length=100)
    designation = models.CharField(max_length=200)
    address_mentioned_in_poa = models.TextField()
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    caf_processed = models.CharField(max_length=3, null=True, blank=True)
    act_status = models.CharField(max_length=3, null=True, blank=True)
    act_remark = models.CharField(max_length=30, null=True, blank=True)

    class Meta:
        managed = False
        app_label= 'apis'
        db_table = "bulk_connection_details"
