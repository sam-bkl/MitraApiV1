from django.db import models

class CtopMaster(models.Model):
    username = models.CharField(max_length=30, null=True)
    ctopupno = models.CharField(max_length=20, null=True)
    name = models.CharField(max_length=100, null=True)
    dealertype = models.CharField(max_length=50, null=True)
    ssa_code = models.CharField(max_length=50, null=True)
    csccode = models.CharField(max_length=50, null=True)
    circle_code = models.CharField(max_length=10, null=True)
    attached_to = models.CharField(max_length=50, null=True)
    contact_number = models.CharField(max_length=50, null=True)
    pos_hno = models.CharField(max_length=100, null=True)
    pos_street = models.CharField(max_length=100, null=True)
    pos_landmark = models.CharField(max_length=100, null=True)
    pos_locality = models.CharField(max_length=100, null=True)
    pos_city = models.CharField(max_length=100, null=True)
    pos_district = models.CharField(max_length=100, null=True)
    pos_state = models.CharField(max_length=100, null=True)
    pos_pincode = models.CharField(max_length=100, null=True)
    created_date = models.DateTimeField(null=True)
    pos_name_ss = models.CharField(max_length=100, null=True)
    pos_owner_name = models.CharField(max_length=100, null=True)
    pos_code = models.CharField(max_length=100, null=True)
    pos_ctop = models.CharField(max_length=100, null=True)
    circle_name = models.CharField(max_length=50, null=True)
    pos_unique_code = models.CharField(max_length=20, primary_key=True)
    latitude = models.TextField(null=True)
    longitude = models.TextField(null=True)
    aadhaar_no = models.CharField(max_length=20, null=True)
    zone_code = models.CharField(max_length=5, null=True)

    class Meta:
        managed = False
        db_table = 'ctop_master'
        app_label= 'apis'

    def __str__(self):
        return self.ctopupno
   
    @property
    def is_authenticated(self):
        """
        Required by Django Rest Framework's IsAuthenticated permission.
        Always returns True for valid JWT-authenticated users.
        """
        return True

class Simprepaid(models.Model):
    simno = models.CharField(max_length=20, db_column='simno', primary_key=True)
    pukno1 = models.CharField(max_length=15, db_column='pukno1', null=True)
    pukno2 = models.CharField(max_length=15, db_column='pukno2', null=True)
    pin1 = models.CharField(max_length=15, db_column='pin1', null=True)
    pin2 = models.CharField(max_length=15, db_column='pin2', null=True)
    location = models.CharField(max_length=50, db_column='location', null=True)
    status = models.IntegerField(db_column='status', null=True)
    issuedate = models.DateTimeField(db_column='issuedate', null=True)
    vendor_code = models.IntegerField(db_column='vendor_code', null=True)
    circle_code = models.IntegerField(db_column='circle_code', null=True)
    circle = models.CharField(max_length=3, db_column='circle', null=True)
    product_code = models.IntegerField(db_column='product_code', null=True)
    imsi = models.BigIntegerField(db_column='imsi', null=True)
    plan_code = models.IntegerField(db_column='plan_code', null=True)
    changed_date = models.DateTimeField(db_column='changed_date', null=True)

    class Meta:
        managed = False
        db_table = 'simprepaid'   # schema + table in lowercase
        app_label= 'apis'

class Simpostpaid(models.Model):
    simno = models.CharField(max_length=19, db_column='simno', primary_key=True)
    pukno1 = models.CharField(max_length=15, db_column='pukno1', null=True)
    pukno2 = models.CharField(max_length=15, db_column='pukno2', null=True)
    pin1 = models.CharField(max_length=10, db_column='pin1', null=True)
    pin2 = models.CharField(max_length=10, db_column='pin2', null=True)
    location = models.CharField(max_length=50, db_column='location', null=True)
    status = models.IntegerField(db_column='status', null=True)
    issuedate = models.DateTimeField(db_column='issuedate', null=True)
    vendor_code = models.IntegerField(db_column='vendor_code', null=True)
    circle_code = models.IntegerField(db_column='circle_code', null=True)
    circle = models.CharField(max_length=3, db_column='circle', null=True)
    product_code = models.IntegerField(db_column='product_code', null=True)
    imsi = models.BigIntegerField(db_column='imsi', null=True)
    plancode = models.IntegerField(db_column='plancode', null=True)
    changed_date = models.DateTimeField(db_column='changed_date', null=True)

    class Meta:
        managed = False
        db_table = 'simpostpaid'   # lowercase table name
        app_label= 'apis'

class GsmChoice(models.Model):
    gsmno = models.CharField(max_length=10, db_column='gsmno', primary_key=True)
    pin = models.CharField(max_length=10, db_column='pin', null=True)
    mobileno = models.CharField(max_length=10, db_column='mobileno', null=True)
    status = models.IntegerField(db_column='status', null=True)
    csccode = models.CharField(max_length=20, db_column='csccode', null=True)
    ssa_code = models.CharField(max_length=20, db_column='ssa_code', null=True)
    circle_code = models.IntegerField(db_column='circle_code', null=True)
    trans_date = models.DateTimeField(db_column='trans_date', null=True)
    data_entry_date = models.DateTimeField(db_column='data_entry_date', null=True)
    remarks = models.CharField(max_length=30, db_column='remarks', null=True)
    ipaddress = models.CharField(max_length=20, db_column='ipaddress', null=True)
    user_agent = models.CharField(max_length=300, db_column='user_agent', null=True)

    class Meta:
        managed = False
        db_table = 'gsm_choice'  # lowercase table name
        app_label= 'apis'

class ApiOtpTable(models.Model):
    ctopupno = models.CharField(max_length=15)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'api_otp_table'
        app_label= 'apis'

class RefOtpTable(models.Model):
    refno = models.CharField(max_length=15)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        managed = False
        db_table = 'ref_otp_table'
        app_label= 'apis'


class AppVersion(models.Model):
    id = models.AutoField(primary_key=True)  # Required internal PK
    version = models.CharField(max_length=15, db_column='version')

    class Meta:
        managed = False         # DO NOT create or modify table
        db_table = 'app_version'
        app_label = 'apis'

    def __str__(self):
        return self.version


class CosBcd(models.Model):
    de_csccode = models.CharField(max_length=150, null=True)
    de_username = models.CharField(max_length=150, null=True)
    dateallottment = models.DateTimeField(null=True)
    gsmnumber = models.CharField(max_length=150,null=True)
    simnumber = models.CharField(max_length=150,primary_key=True)
    caf_serial_no = models.CharField(max_length=30, null=True)
    connection_type = models.IntegerField(null=True)
    name = models.CharField(max_length=150, null=True)
    middle_name = models.CharField(max_length=150, null=True)
    last_name = models.CharField(max_length=150, null=True)
    f_h_name = models.CharField(max_length=300, null=True)
    gender = models.CharField(max_length=24, null=True)
    date_of_birth = models.DateTimeField(null=True)
    local_addr_hno = models.CharField(max_length=600, null=True)
    local_addr_street = models.CharField(max_length=600, null=True)
    local_addr_locality = models.CharField(max_length=600, null=True)
    local_addr_city = models.CharField(max_length=150, null=True)
    local_addr_state = models.CharField(max_length=90, null=True)
    local_addr_pin = models.IntegerField(null=True)
    perm_addr_hno = models.CharField(max_length=600, null=True)
    perm_addr_street = models.CharField(max_length=600, null=True)
    perm_addr_locality = models.CharField(max_length=600, null=True)
    perm_addr_city = models.CharField(max_length=150, null=True)
    perm_addr_state = models.CharField(max_length=150, null=True)
    perm_addr_pin = models.IntegerField(null=True)
    billing_address = models.CharField(max_length=750, null=True)
    customer_type = models.CharField(max_length=300, null=True)
    nationality = models.CharField(max_length=60, null=True)
    country = models.CharField(max_length=90, null=True)
    visa_expiry_date = models.DateTimeField(null=True)
    email = models.CharField(max_length=150, null=True)
    photo_id_doc = models.IntegerField(null=True)
    photo_id_sno = models.CharField(max_length=75, null=True)
    photo_id_issue_date = models.DateTimeField(null=True)
    photo_id_issue_auth = models.CharField(max_length=150, null=True)
    photo_id_issue_place = models.CharField(max_length=75, null=True)
    address_id_doc = models.IntegerField(null=True)
    address_id_sno = models.CharField(max_length=150, null=True)
    address_id_issue_date = models.DateTimeField(null=True)
    address_id_issue_auth = models.CharField(max_length=150, null=True)
    address_id_issue_place = models.CharField(max_length=150, null=True)
    distinct_operators = models.IntegerField(null=True)
    other_connection_det = models.CharField(max_length=450, null=True)
    services = models.CharField(max_length=300, null=True)
    alternate_contact_no = models.BigIntegerField(null=True)
    bsnl_telno = models.CharField(max_length=75, null=True)
    other_telno = models.CharField(max_length=75, null=True)
    profession = models.CharField(max_length=60, null=True)
    organisation = models.CharField(max_length=90, null=True)
    mar_status = models.CharField(max_length=60, null=True)
    qualification = models.CharField(max_length=69, null=True)
    imsi_old = models.BigIntegerField(null=True)
    pan_gir_uid = models.CharField(max_length=60, null=True)
    local_ref = models.CharField(max_length=750, null=True)
    local_ref_contact = models.CharField(max_length=36, null=True)
    plan_code = models.IntegerField(null=True)
    levelno = models.IntegerField(null=True)
    benefitvalidity = models.DateTimeField(null=True)
    servicetax = models.DecimalField(max_digits=19, decimal_places=4, null=True)
    plancharge = models.DecimalField(max_digits=19, decimal_places=4, null=True)
    levelamount = models.IntegerField(null=True)
    advancerent = models.IntegerField(null=True)
    totalamount = models.DecimalField(max_digits=19, decimal_places=4, null=True)
    commission = models.IntegerField(null=True)
    netamount = models.IntegerField(null=True)
    footnoteremarks1 = models.CharField(max_length=1800, null=True)
    receiptno = models.CharField(max_length=150, null=True)
    stdpco = models.CharField(max_length=150, null=True)
    workorder = models.CharField(max_length=150, null=True)
    caf_avail = models.CharField(max_length=60, null=True)
    caf_rejected = models.CharField(max_length=3, null=True)
    caf_recd_date = models.DateTimeField(null=True)
    intd_flag = models.IntegerField(null=True)
    checked_yn = models.CharField(max_length=3, null=True)
    flag = models.IntegerField(null=True)
    flag_date = models.DateTimeField(null=True)
    msc = models.CharField(max_length=90, null=True)
    in_plan_id = models.CharField(max_length=60, null=True)
    in_code = models.CharField(max_length=60, null=True)
    dummy_sim = models.CharField(max_length=3, null=True)
    og_enable = models.CharField(max_length=3, null=True)
    dnc = models.CharField(max_length=3, null=True)
    act_type = models.CharField(max_length=150, null=True)
    paymenttype = models.CharField(max_length=3, null=True)
    dd_details = models.CharField(max_length=300, null=True)
    bank_details = models.CharField(max_length=450, null=True)
    submitted_date = models.DateTimeField(null=True)
    tariff_plan_app = models.CharField(max_length=90, null=True)
    vas_app = models.CharField(max_length=90, null=True)
    tariff_plan_gprs_mms = models.CharField(max_length=60, null=True)
    sales_channel_id = models.IntegerField(null=True)
    subscr_id = models.IntegerField(null=True)
    upc_code = models.CharField(max_length=30, null=True)
    prev_optr = models.CharField(max_length=60, null=True)
    ruim_no = models.CharField(max_length=60, null=True)
    order_id = models.CharField(max_length=60, null=True)
    level1date = models.DateTimeField(null=True)
    level2date = models.DateTimeField(null=True)
    completed_by = models.CharField(max_length=90, null=True)
    circle_code = models.IntegerField(null=True)
    activation_csccode = models.CharField(max_length=60, null=True)
    activation_username = models.CharField(max_length=60, null=True)
    activation_mobileno = models.CharField(max_length=36, null=True)
    activation_date = models.DateTimeField(null=True)
    hlr_init_act_date = models.DateTimeField(null=True)
    tele_ver_agent_code = models.CharField(max_length=60, null=True)
    tele_ver_date = models.DateTimeField(null=True)
    tele_ver_remarks = models.CharField(max_length=300, null=True)
    hlr_final_act_date = models.DateTimeField(null=True)
    activation_status = models.CharField(max_length=6, null=True)
    activation_remarks = models.CharField(max_length=900, null=True)
    hlr_init_sent_date = models.DateTimeField(null=True)
    hlr_final_sent_date = models.DateTimeField(null=True)
    ss_cug_id = models.IntegerField(null=True)
    account_type = models.CharField(max_length=60, null=True)
    connection_no = models.IntegerField(null=True)
    category_code = models.IntegerField(null=True)
    product_code = models.IntegerField(null=True)
    converted = models.IntegerField(null=True)
    uid_no = models.CharField(max_length=12, null=True)
    gstin_no = models.CharField(max_length=150, null=True)
    gst_registered_address = models.CharField(max_length=600, null=True)
    gst_state_code = models.CharField(max_length=60, null=True)
    gst_pin = models.BigIntegerField(null=True)
    blg_gst_updt = models.DateTimeField(null=True)
    status = models.CharField(max_length=30, null=True)
    ssa_code = models.CharField(max_length=30, null=True)
    pos_mobile_no = models.CharField(max_length=300, null=True)
    package_id = models.CharField(max_length=30, null=True)
    tvplan_act_date = models.DateTimeField(null=True)
    tvplan_act_remarks = models.CharField(max_length=600, null=True)
    tvplan_deact_date = models.DateTimeField(null=True)
    tvplan_deact_remarks = models.CharField(max_length=600, null=True)
    account_no = models.CharField(max_length=45, null=True)
    doptr = models.CharField(max_length=30, null=True)
    remarks = models.CharField(max_length=600, null=True)
    alternate_contact_own = models.CharField(max_length=30, null=True)
    tracking_id = models.IntegerField(null=True)
    sdp_activation_status = models.CharField(max_length=30, null=True)
    sdp_activation_date = models.DateTimeField(null=True)
    full_mnp = models.CharField(max_length=6, null=True)
    account_category = models.IntegerField(null=True)
    gateway_date = models.DateTimeField(null=True)
    doptr_circle_code = models.CharField(max_length=6, null=True)
    billing_mnp_date = models.DateTimeField(null=True)
    mnp_edit_date = models.DateTimeField(null=True)
    is_bill_submit = models.IntegerField(null=True)
    msisdn_type = models.IntegerField(null=True)
    sim_type = models.IntegerField(null=True)
    cmf_account_category = models.IntegerField(null=True)
    cmf_bill_state = models.CharField(max_length=300, null=True)
    cmf_bill_fmt_opt = models.IntegerField(null=True)
    cmf_bill_disp_meth = models.IntegerField(null=True)
    cmf_rate_class_default = models.IntegerField(null=True)
    cmf_exrate_class = models.IntegerField(null=True)
    cmf_mkt_code = models.IntegerField(null=True)
    cmf_vip_code = models.IntegerField(null=True)
    cmf_acct_seg_id = models.IntegerField(null=True)
    cmf_bill_period = models.CharField(max_length=300, null=True)
    zone_element_id = models.IntegerField(null=True)
    invs_saleschannel_id = models.IntegerField(null=True)
    print_service_center_id = models.IntegerField(null=True)
    imsi = models.CharField(max_length=60, null=True)
    primary_talk_value = models.IntegerField(null=True)
    freebies = models.CharField(max_length=60, null=True)
    simstate = models.CharField(max_length=45, null=True)
    emf_config_id = models.IntegerField(null=True)
    ins_usr = models.CharField(max_length=300, null=True)
    om_remarks = models.CharField(max_length=3000, null=True)
    remarks_wdi = models.CharField(max_length=300, null=True)
    mnp_process_date = models.DateTimeField(null=True)
    timeallottment = models.DateTimeField(null=True)
    in_status = models.CharField(max_length=15, null=True)
    inserted_time = models.DateTimeField(null=True)
    final_act_update_time = models.DateTimeField(null=True)
    pdf_submission = models.CharField(max_length=60, null=True)
    csv_submission = models.CharField(max_length=60, null=True)
    ss_group_id = models.CharField(max_length=150, null=True)
    column1 = models.CharField(max_length=60, null=True)
    column2 = models.CharField(max_length=60, null=True)
    column3 = models.CharField(max_length=60, null=True)
    column4 = models.CharField(max_length=60, null=True)
    pwd = models.CharField(max_length=9, null=True)
    photo = models.BinaryField(null=True, blank=True) 
    photo_aadhaar = models.BinaryField(null=True, blank=True) 
    photo_pos = models.BinaryField(null=True, blank=True)
    unq_resp_code_pos = models.CharField(max_length=60, null=True)
    unq_resp_code_cust = models.CharField(max_length=60, null=True)
    unq_resp_date_pos = models.DateTimeField(null=True)
    unq_resp_date_cust = models.DateTimeField(null=True)
    device_ip = models.CharField(max_length=30, null=True)
    device_mac = models.CharField(max_length=50, null=True)
    verified_flag = models.CharField(max_length=150, null=True)
    latitude = models.CharField(max_length=50, null=True)
    longitude = models.CharField(max_length=50, null=True)
    app_version = models.CharField(max_length=10, null=True)
    live_photo_time = models.DateTimeField(null=True)
    pos_adh_name = models.CharField(max_length=150, null=True)
    subscriber_type = models.CharField(max_length=50, null=True)
    circle_code = models.CharField(max_length=50, null=True)
    local_ref_name= models.CharField(max_length=150, null=True)
    ref_careof_address= models.CharField(max_length=200, null=True)
    ref_landmark= models.CharField(max_length=200, null=True)
    ref_district= models.CharField(max_length=150, null=True)
    upcvalidupto = models.DateTimeField(null=True)
    caf_type = models.CharField(max_length=50,null=True)
    ref_otp = models.CharField(max_length=10, null=True)
    ref_otp_time = models.DateTimeField(null=True)

    class Meta:
        managed = False
        db_table = 'cos_bcd'
        app_label = 'apis'

# class AppVersion(models.Model):
#     version = models.CharField(max_length=15)
#     def __str__(self):
#         return self.version
