from rest_framework import serializers

class SendOtpSerializer(serializers.Serializer):
    gsmnumber = serializers.CharField(
        max_length=15,
        required=True
    )
    purpose = serializers.CharField(
        max_length=50,
        required=True
    )

    def validate_purpose(self, value):
        allowed = {
            "POST2PRE",
            "PRE2POST",
            "Login",
            "sim swap",
            "reverification"
        }
        #value = value.upper()
        if value not in allowed:
            raise serializers.ValidationError("Invalid OTP purpose")
        return value
    
class VerifyOtpSerializer(serializers.Serializer):
    gsmnumber = serializers.CharField(
        max_length=30,
        required=True
    )
    purpose = serializers.CharField(
        max_length=50,
        required=True
    )
    otp = serializers.CharField(
        max_length=6,
        required=True
    )

    # def validate_purpose(self, value):
    #     return value.upper()

    def validate_otp(self, value):
        if not value.isdigit() or len(value) != 6:
            raise serializers.ValidationError("OTP must be 6 digits")
        return value
