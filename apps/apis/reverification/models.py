from django.db import models

class ReverifyDataUpload(models.Model):
    sno = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)
    mobile_no = models.CharField(max_length=20, null=True, blank=True)
    sim_no = models.CharField(max_length=100, null=True, blank=True)
    imsi_no = models.CharField(max_length=100, null=True, blank=True)
    caf_no = models.CharField(max_length=20, null=True, blank=True)
    circle_code = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)
    ssa_code = models.CharField(max_length=10, null=True, blank=True)
    upload_date = models.CharField(max_length=20, null=True, blank=True)
    user_id = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=30, null=True, blank=True)
    sms_sent = models.CharField(max_length=3, null=True, blank=True)
    sms_sent_count = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)
    sms_sent_dt = models.DateTimeField(null=True, blank=True)
    pos_code = models.CharField(max_length=50, null=True, blank=True)
    reverify_date_time = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    no_request_from = models.CharField(max_length=20, null=True, blank=True)
    ss_moved = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)
    data_ins_date = models.DateTimeField(null=True, blank=True)
    ssa_code_circle = models.CharField(max_length=20, null=True, blank=True)
    tid = models.CharField(max_length=30, primary_key=True)
    file_id = models.CharField(max_length=30, null=True, blank=True)
    caf_type = models.CharField(max_length=30, primary_key=True)

    class Meta:
        managed = False
        db_table = "reverify_data_upload"
        app_label = 'apis'

class RevEkycDetails(models.Model):
    id = models.AutoField(primary_key=True)

    new_caf_id = models.CharField(max_length=25, null=True, blank=True)
    gsmnumber = models.CharField(max_length=20)
    otp = models.CharField(max_length=10)

    verified_at = models.DateTimeField(null=True, blank=True)
    purpose = models.CharField(max_length=50, null=True, blank=True)
    mobile_no = models.CharField(max_length=20, null=True, blank=True)
    circle_code = models.CharField(max_length=10, null=True, blank=True)
    sim_no = models.CharField(max_length=30, null=True, blank=True)
    imsi_no = models.CharField(max_length=30, null=True, blank=True)
    caf_no = models.CharField(max_length=50, null=True, blank=True)
    upload_date = models.DateTimeField(null=True, blank=True)
    no_request_from = models.CharField(max_length=50, null=True, blank=True)
    caf_type = models.CharField(max_length=20, null=True, blank=True)

    # -------- SS fields --------
    ss_account_no = models.CharField(max_length=50, null=True, blank=True)
    ss_bill_fname = models.CharField(max_length=150, null=True, blank=True)
    ss_bill_lname = models.CharField(max_length=150, null=True, blank=True)
    ss_bill_minit = models.CharField(max_length=50, null=True, blank=True)
    ss_address1 = models.CharField(max_length=255, null=True, blank=True)
    ss_address2 = models.CharField(max_length=255, null=True, blank=True)
    ss_address3 = models.CharField(max_length=255, null=True, blank=True)
    ss_city = models.CharField(max_length=100, null=True, blank=True)
    ss_state = models.CharField(max_length=50, null=True, blank=True)
    ss_zip = models.CharField(max_length=20, null=True, blank=True)
    ss_in_active_date = models.DateTimeField(null=True, blank=True)
    ss_emf_config_id = models.CharField(max_length=50, null=True, blank=True)
    ss_connection_type = models.CharField(max_length=50, null=True, blank=True)
    ss_uid_no = models.CharField(max_length=50, null=True, blank=True)
    ss_customer_uid_token = models.CharField(max_length=150, null=True, blank=True)
    ss_act_type = models.CharField(max_length=50, null=True, blank=True)
    ss_acc_balance = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    ss_sim_number = models.CharField(max_length=30, null=True, blank=True)
    ss_amount_req = models.CharField(max_length=10, null=True, blank=True)
    ss_caf_serial_no = models.CharField(max_length=50, null=True, blank=True)
    ss_ssa_code = models.CharField(max_length=50, null=True, blank=True)
    remarks = models.CharField(max_length=300, null=True, blank=True)
    customer_type = models.CharField(max_length=100, null=True, blank=True)
    ss_group_id = models.CharField(max_length=100, null=True, blank=True)

    # -------- audit fields --------
    insert_time = models.DateTimeField(auto_now_add=False)
    insert_username = models.CharField(max_length=100, null=True, blank=True)


    class Meta:
        managed = False
        db_table = "rev_ekyc_details"
        app_label = 'apis'
