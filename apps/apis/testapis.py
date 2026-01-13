from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.permissions import IsAuthenticated , AllowAny
from .models import CtopMaster,Simprepaid, Simpostpaid, GsmChoice ,ApiOtpTable, AppVersion,RefOtpTable,CosBcd,FrcPlan,SimpostpaidSold,SimprepaidSold
from .serializers import CtopMasterSerializer,SimprepaidSerializer,SimpostpaidSerializer,GsmChoiceSerializer,AppVersionSerializer
import random
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.cache import cache
from .send_sms import send_sms, ref_send_sms
from django.utils import timezone
from datetime import datetime, timedelta
import requests,json
import time
from django.utils.timezone import now
from django.db import transaction
from django.db.models import Q
from django.forms.models import model_to_dict

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_prepaid_test(request):
    """
    Expected POST:
    {
        "last5": "12345",
        "vendor_code": "V001"
    }
    """
    last5 = request.data.get('last5', '').strip()
    vendor_code = request.data.get('vendor_code', '').strip()

    # Validate last5
    if not last5 or len(last5) != 5 or not last5.isdigit():
        return Response(
            {
                'status': "failure",
                "message": "A valid 5-digit 'last5' value is required",
                "data": None
            },
            status=status.HTTP_200_OK
        )

    # Validate vendor_code
    if not vendor_code:
        return Response(
            {
                'status': "failure",
                "message": "'vendor_code' is required",
                "data": None
            },
            status=status.HTTP_200_OK
        )

    try:
        with transaction.atomic():
            sims = Simprepaid.objects.filter(
                status=1,
                location=vendor_code,
                simno__endswith=last5
            )

            if not sims.exists():
                return Response(
                    {
                        "status": "failure",
                        "message": "No matching SIM found",
                        "data": []
                    },
                    status=status.HTTP_200_OK
                )

            serializer = SimprepaidSerializer(sims, many=True)

            # Return only simno list (clean output)
            simnos = [{"simno": item["simno"]} for item in serializer.data]

            return Response(
                {
                    "status": "success",
                    "message": f"{len(simnos)} SIM(s) found",
                    "data": simnos
                },
                status=status.HTTP_200_OK
            )

    except Exception as e:
        return Response(
            {
                "status": "failure",
                "message": "Internal server error",
                "error": str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
