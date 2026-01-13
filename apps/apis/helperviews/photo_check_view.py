from django.db import transaction
from datetime import datetime, time
from django.utils import timezone
from django.db import transaction
from rest_framework.response import Response
from rest_framework import status as http_status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .photo_check_functions import *
from ..serializers import KycImageSerializer

@api_view(['POST'])
def verify_selfie(request):
    serializer = KycImageSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    image = base64_to_image(serializer.validated_data['image_base64'])
    valid, error = validate_image(image)
    if not valid:
        return Response({"error": error}, status=400)

    response = {
        "face_detected": detect_face(image),
        "white_background": is_white_background(image),
        "not_blurry": is_not_blurry(image),
        "shadows_ok": shadows_ok(image),
    }

    response["kyc_pass"] = all(response.values())

    return Response(response)