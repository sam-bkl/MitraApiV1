from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import ReverifyDataUpload
from .serializers import ReverifyLookupInputSerializer, ReverifyLookupOutputSerializer

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reverify_lookup(request):
    # -----------------------------
    # 1. Validate input
    # -----------------------------
    serializer = ReverifyLookupInputSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    mobile_no = serializer.validated_data["mobile_no"]
    circle_code = serializer.validated_data["circle_code"]

    # -----------------------------
    # 2. Query DB
    # -----------------------------
    record = (
        ReverifyDataUpload.objects
        .filter(
            mobile_no=mobile_no,
            circle_code=circle_code
        )
        .order_by("-reverify_date_time")
        .first()
    )

    if not record:
        return Response(
            {"message": "No reverify data found"},
            status=status.HTTP_404_NOT_FOUND
        )

    # -----------------------------
    # 3. Serialize output
    # -----------------------------
    output = ReverifyLookupOutputSerializer(record)
    return Response(output.data, status=status.HTTP_200_OK)
