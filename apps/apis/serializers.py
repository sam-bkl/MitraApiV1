from rest_framework import serializers
from .models import CtopMaster,Simprepaid, Simpostpaid, GsmChoice, AppVersion, CosBcd

class CtopMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CtopMaster
        fields = '__all__'

class SimprepaidSerializer(serializers.ModelSerializer):
    class Meta:
        model = Simprepaid
        fields = '__all__'


class SimpostpaidSerializer(serializers.ModelSerializer):
    class Meta:
        model = Simpostpaid
        fields = '__all__'


class GsmChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = GsmChoice
        fields = '__all__'

class AppVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppVersion
        fields = ['version']

class CosBcdSerializer(serializers.ModelSerializer):
    class Meta:
        model = CosBcd
        fields = '__all__'

class KycImageSerializer(serializers.Serializer):
    image_base64 = serializers.CharField()