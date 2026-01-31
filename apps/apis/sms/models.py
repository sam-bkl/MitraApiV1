from django.db import models

class SmAppOtp(models.Model):
    id = models.AutoField(primary_key=True)
    identifier = models.CharField(max_length=30)
    otp = models.CharField(max_length=6)
    purpose = models.CharField(max_length=50)
    created_at = models.DateTimeField()
    is_used = models.BooleanField()
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        app_label = 'apis'
        db_table = "sm_app_otp"
