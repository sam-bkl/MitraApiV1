from django.db import models


class Esimprepaid(models.Model):
    simno = models.CharField(max_length=20,  primary_key=True)
    imsi = models.CharField(max_length=15, null=True, blank=True)

    pukno1 = models.CharField(max_length=15, null=True, blank=True)
    pukno2 = models.CharField(max_length=15, null=True, blank=True)

    pin1 = models.CharField(max_length=15, null=True, blank=True)
    pin2 = models.CharField(max_length=15, null=True, blank=True)

    status = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)
    circle_code = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)

    changed_date = models.DateTimeField(null=True, blank=True)

    qr_code = models.BinaryField(null=True, blank=True)

    dual_imsi = models.CharField(max_length=1, null=True, blank=True)
    file_id = models.CharField(max_length=20, null=True, blank=True)
    plan_code = models.CharField(max_length=20, null=True, blank=True)


    class Meta:
        managed = False
        db_table = "esimprepaid"
        app_label = "apis"


class EsimprepaidSold(models.Model):
    simno = models.CharField(max_length=20,  primary_key=True)
    imsi = models.CharField(max_length=15, null=True, blank=True)

    pukno1 = models.CharField(max_length=15, null=True, blank=True)
    pukno2 = models.CharField(max_length=15, null=True, blank=True)

    pin1 = models.CharField(max_length=15, null=True, blank=True)
    pin2 = models.CharField(max_length=15, null=True, blank=True)

    status = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)
    circle_code = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)

    changed_date = models.DateTimeField(null=True, blank=True)

    qr_code = models.BinaryField(null=True, blank=True)

    dual_imsi = models.CharField(max_length=1, null=True, blank=True)
    file_id = models.CharField(max_length=20, null=True, blank=True)
    plan_code = models.CharField(max_length=20, null=True, blank=True)


    class Meta:
        managed = False
        db_table = "esimprepaid_sold"
        app_label = "apis"



class Esimpostpaid(models.Model):
    simno = models.CharField(max_length=20, primary_key=True)
    imsi = models.CharField(max_length=15, null=True, blank=True)

    pukno1 = models.CharField(max_length=15, null=True, blank=True)
    pukno2 = models.CharField(max_length=15, null=True, blank=True)

    pin1 = models.CharField(max_length=15, null=True, blank=True)
    pin2 = models.CharField(max_length=15, null=True, blank=True)

    status = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)
    circle_code = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)

    changed_date = models.DateTimeField(null=True, blank=True)

    qr_code = models.BinaryField(null=True, blank=True)

    dual_imsi = models.CharField(max_length=1, null=True, blank=True)
    file_id = models.CharField(max_length=20, null=True, blank=True)
    plan_code = models.CharField(max_length=20, null=True, blank=True)


    class Meta:
        managed = False
        db_table = "esimpostpaid"
        app_label = "apis"


class EsimpostpaidSold(models.Model):
    simno = models.CharField(max_length=20, primary_key=True)
    imsi = models.CharField(max_length=15, null=True, blank=True)

    pukno1 = models.CharField(max_length=15, null=True, blank=True)
    pukno2 = models.CharField(max_length=15, null=True, blank=True)

    pin1 = models.CharField(max_length=15, null=True, blank=True)
    pin2 = models.CharField(max_length=15, null=True, blank=True)

    status = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)
    circle_code = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)

    changed_date = models.DateTimeField(null=True, blank=True)

    qr_code = models.BinaryField(null=True, blank=True)

    dual_imsi = models.CharField(max_length=1, null=True, blank=True)
    file_id = models.CharField(max_length=20, null=True, blank=True)
    plan_code = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        managed = False
        db_table = "esimpostpaid_sold"
        app_label = "apis"

class EmailOtpTable(models.Model):
    id = models.AutoField(primary_key=True)
    email_id = models.CharField(max_length=150)
    otp = models.CharField(max_length=6)
    purpose = models.CharField(max_length=25, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "email_otp_table"
        app_label = "apis"