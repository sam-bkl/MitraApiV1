from rest_framework import serializers
from .models import ReverifyDataUpload

class ReverifyLookupInputSerializer(serializers.Serializer):
    mobile_no = serializers.CharField(max_length=20, required=True)
    circle_code = serializers.IntegerField(required=True)

class ReverifyLookupOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReverifyDataUpload
        fields = (
            "mobile_no",
            "circle_code",
            "sim_no",
            "imsi_no",
            "caf_no",
            "upload_date",
            "no_request_from",
            "caf_type",
        )
