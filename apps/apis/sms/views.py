from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.permissions import IsAuthenticated , AllowAny
from django.utils import timezone
from datetime import timedelta
from .models import SmAppOtp
from .helper_functions import generate_otp,choose_sms_gateway,send_sms
from .serializers import SendOtpSerializer,VerifyOtpSerializer


OTP_EXPIRY_SECONDS = 600       # 10 minutes
OTP_RESEND_COOLDOWN = 30       # 30 seconds

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def app_send_otp(request):
    serializer = SendOtpSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    identifier = serializer.validated_data["gsmnumber"]
    purpose = serializer.validated_data["purpose"]

    if not identifier or not purpose:
        return Response(
            {"status": "error", "message": "identifier and purpose are required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    now = timezone.now()

    last_otp = SmAppOtp.objects.filter(
        identifier=identifier,
        purpose=purpose,
        is_used=False
    ).order_by("-created_at").first()
    is_resend = last_otp is not None
    # Cooldown
    if last_otp:
        elapsed = (now - last_otp.created_at).total_seconds()
        if elapsed < OTP_RESEND_COOLDOWN:
            return Response(
                {
                    "status": "error",
                    "message": "Please wait before requesting OTP again",
                    "wait_seconds": int(OTP_RESEND_COOLDOWN - elapsed)
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        # Expire old OTP explicitly
        last_otp.is_used = True
        last_otp.save(update_fields=["is_used"])

    otp = generate_otp()

    SmAppOtp.objects.create(
        identifier=identifier,
        otp=otp,
        purpose=purpose,
        created_at=now,
        expires_at=now + timedelta(seconds=OTP_EXPIRY_SECONDS),
        is_used=False
    )

    gateway = choose_sms_gateway(is_resend)
    send_sms(identifier, otp,purpose, gateway)  

    return Response(
        {
            "status": "success",
            "message": "OTP sent successfully",
            "gsmnumber": identifier,
            "purpose": purpose
        },
        status=status.HTTP_200_OK
    )

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def app_verify_otp(request):
    serializer = VerifyOtpSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    identifier = serializer.validated_data["gsmnumber"]
    purpose = serializer.validated_data["purpose"]
    otp = serializer.validated_data["otp"]

    if not identifier or not purpose or not otp:
        return Response(
            {
                "status": "failure",
                "message": "identifier, purpose and otp are required"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    otp_record = SmAppOtp.objects.filter(
        identifier=identifier,
        purpose=purpose,
        otp=otp,
        is_used=False,
        expires_at__gt=timezone.now()
    ).order_by("-created_at").first()

    if not otp_record:
        return Response(
            {
                "status": "failure",
                "message": "Invalid or expired OTP"
            },
            status=status.HTTP_200_OK
        )

    # Mark OTP as used
    otp_record.is_used = True
    otp_record.save(update_fields=["is_used"])

    return Response(
        {
            "status": "success",
            "message": "OTP verified successfully",
            "gsmnumber": identifier,
            "purpose": purpose,
            "otp": otp,
            "verified_at": timezone.now()
        },
        status=status.HTTP_200_OK
    )