from django.db import models


class Esimprepaid(models.Model):
    simno = models.CharField(max_length=20, null=True, primary_key=True)
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

    class Meta:
        managed = False
        db_table = "esimprepaid"
        app_label = "apis"


class EsimprepaidSold(models.Model):
    simno = models.CharField(max_length=20, null=True, primary_key=True)
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

    class Meta:
        managed = False
        db_table = "esimprepaid_sold"
        app_label = "apis"