import random
from django.core.mail import send_mail
from django.conf import settings


def send_email_otp(to_email: str) -> str:
    otp = str(random.randint(100000, 999999))

    send_mail(
        subject="BSNL OTP Verification",
        message=f"Your OTP is {otp}. Valid for 10 minutes.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to_email],
        fail_silently=False,
    )

    return otp