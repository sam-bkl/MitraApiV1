from rest_framework import serializers
from .models import SimUpgradeRequest,AppUpgradeOptions



class SimUpgradeRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = SimUpgradeRequest
        fields = '__all__'
    
class AppUpgradeOptionsSerializer(serializers.ModelSerializer):

    class Meta:
        model = AppUpgradeOptions
        fields = ("id", "upg_label", "value")

class SimUpgradeRequestListSerializer(serializers.ModelSerializer):

    status = serializers.SerializerMethodField()

    class Meta:
        model = SimUpgradeRequest
        fields = (
            "id",
            "mobile_number",
            "process_type",
            "connection_type",
            "exchange_reason",
            "sim_number",
            "caf_serial_no",
            "ssa_code",
            "created_at",
            "insert_user",
            "status",  # 👈 added
        )

    def get_status(self, obj):
        status_map = self.context.get("oracle_status_map", {})
        return status_map.get(obj.mobile_number, "PENDING")