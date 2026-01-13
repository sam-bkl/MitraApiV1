from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Esimprepaid
from .serializers import EsimprepaidSerializer


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def get_esim_by_simnumber(request):
    """
    POST body:
    {
        "simnumber": "8991555074590274058"
    }
    """

    simnumber = request.data.get("simnumber")

    if not simnumber:
        return Response(
            {
                "status": "failure",
                "message": "simnumber is required"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    records = Esimprepaid.objects.filter(simno=simnumber)

    if not records.exists():
        return Response(
            {
                "status": "failure",
                "message": "No eSIM record found",
                "simnumber": simnumber
            },
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = EsimprepaidSerializer(records, many=True)

    return Response(
        {
            "status": "success",
            "count": records.count(),
            "data": serializer.data
        },
        status=status.HTTP_200_OK
    )
