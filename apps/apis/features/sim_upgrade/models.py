from django.db import models

class SimUpgradeRequest(models.Model):

    id = models.BigAutoField(primary_key=True)

    # =========================
    # Request level
    # =========================
    process_type = models.CharField(max_length=20, null=True, blank=True)
    connection_type = models.IntegerField(null=True, blank=True)

    exchange_reason = models.CharField(max_length=50, null=True, blank=True)
    exchange_reason_id = models.CharField(max_length=50, null=True, blank=True)

    csc_code = models.CharField(max_length=50, null=True, blank=True)
    mobile_number = models.CharField(max_length=15, null=True, blank=True)
    sim_type = models.IntegerField(null=True, blank=True)
    is_otp_verified = models.BooleanField(default=False)
    otp_received = models.CharField(max_length=10, null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    # =========================
    # SIM / IMSI
    # =========================
    imsi = models.CharField(max_length=30, null=True, blank=True)
    imsi_old = models.CharField(max_length=30, null=True, blank=True)
    sim_number = models.CharField(max_length=30, null=True, blank=True)
    sim_type = models.IntegerField(null=True, blank=True)
    # =========================
    # Billing / Customer
    # =========================
    account_no = models.CharField(max_length=30, null=True, blank=True)

    bill_fname = models.CharField(max_length=100, null=True, blank=True)
    bill_lname = models.CharField(max_length=100, null=True, blank=True)
    bill_minit = models.CharField(max_length=10, null=True, blank=True)

    bill_address1 = models.TextField(null=True, blank=True)
    bill_address2 = models.TextField(null=True, blank=True)
    bill_address3 = models.TextField(null=True, blank=True)

    bill_city = models.CharField(max_length=100, null=True, blank=True)
    bill_state = models.CharField(max_length=50, null=True, blank=True)
    bill_zip = models.IntegerField(null=True, blank=True)

    # =========================
    # SS / Account Info
    # =========================
    in_active_date = models.DateTimeField(null=True, blank=True)
    emf_config_id = models.CharField(max_length=50, null=True, blank=True)

    ss_connection_type = models.CharField(max_length=20, null=True, blank=True)
    uid_no = models.CharField(max_length=30, null=True, blank=True)
    customer_uid_token = models.CharField(max_length=100, null=True, blank=True)

    act_type = models.CharField(max_length=50, null=True, blank=True)
    acc_balance = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )

    ss_simnumber = models.CharField(max_length=30, null=True, blank=True)
    amount_req = models.CharField(max_length=10, null=True, blank=True)

    caf_serial_no = models.CharField(max_length=30, null=True, blank=True)
    ssa_code = models.CharField(max_length=20, null=True, blank=True)

    remarks = models.CharField(max_length=200, null=True, blank=True)
    alternate_mobile_number = models.CharField(max_length=20, null=True, blank=True)

    # =========================
    # Circle / POS
    # =========================
    cust_circle_code = models.IntegerField(null=True, blank=True)
    pos_circle_code = models.IntegerField(null=True, blank=True)

    # =========================
    # Audit / Control
    # =========================
    parent_ctop_number = models.CharField(max_length=20, null=True, blank=True)
    mpin = models.CharField(max_length=50, null=True, blank=True)

    insert_user = models.CharField(max_length=50, null=True, blank=True)
    ins_user_ip = models.CharField(max_length=50, null=True, blank=True)

    insert_date = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    oif = models.CharField(max_length=1, default="0")
    ora_ins_time = models.DateTimeField(null=True, blank=True)
    activation_type = models.CharField(max_length=25, null=True, blank=True)

    class Meta:
        managed = False
        db_table = "sim_upgrade_request"
        app_label = "apis"

class AppUpgradeOptions(models.Model):
    id = models.BigAutoField(primary_key=True)
    upg_label = models.CharField(max_length=150, null=True, blank=True)
    value = models.CharField(max_length=50, null=True, blank=True)
    circle_code = models.CharField(max_length=3, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "app_upgrade_options"
        app_label = 'apis'