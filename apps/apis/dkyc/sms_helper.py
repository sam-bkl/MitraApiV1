import random
from django.utils import timezone
from datetime import timedelta

OTP_EXPIRY_SECONDS = 600
OTP_RESEND_COOLDOWN = 30


def send_otp(model, field_name, number, sms_func):
    otp = str(random.randint(100000, 999999))

    model.objects.create(
        **{field_name: number, "otp": otp}
    )

    sms_func(number, otp)

    return otp


def verify_otp(model, field_name, number, otp):
    record = model.objects.filter(
        **{field_name: number, "otp": otp}
    ).order_by("-created_at").first()

    if not record:
        return False, "Invalid OTP"

    age = (timezone.now() - record.created_at).total_seconds()
    if age > OTP_EXPIRY_SECONDS:
        record.delete()
        return False, "OTP expired"

    return True, "OTP verified"


def can_resend(model, field_name, number):
    last = model.objects.filter(
        **{field_name: number}
    ).order_by("-created_at").first()

    if not last:
        return True, 0

    elapsed = (timezone.now() - last.created_at).total_seconds()
    if elapsed < OTP_RESEND_COOLDOWN:
        return False, int(OTP_RESEND_COOLDOWN - elapsed)

    return True, 0
