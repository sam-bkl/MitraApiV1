# serializers.py
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from apps.apis.helperviews.sim_swap_allow import map_caf_type_to_category,get_bcd_details_by_gsm
import cx_Oracle

class CustomerInfoSerializer(serializers.Serializer):
    gsm = serializers.CharField(max_length=20)
    circle = serializers.CharField(max_length=10)
    req_type = serializers.CharField(max_length=20)

pools = {}

def get_pool(zone: str):
    if zone not in pools:
        if zone == "SZ":
            pools[zone] = cx_Oracle.SessionPool(
                user="ONBOARDKL",
                password="Onboard_KL2025",
                dsn="10.19.238.38/SIMSOFT",
                min=2, max=10, increment=1, threaded=True
            )
        elif zone == "WZ":
            pools[zone] = cx_Oracle.SessionPool(
                user="ONBOARDKL",
                password="Onboard_KL2025",
                dsn="10.102.187.103/SSDB11",
                min=2, max=10, increment=1, threaded=True
            )
        elif zone == "EZ":
            pools[zone] = cx_Oracle.SessionPool(
                user="ONBOARDKL",
                password="Onboard_KL2025",
                dsn="10.189.1.3/sseast",
                min=2, max=10, increment=1, threaded=True
            )
        elif zone == "NZ":
            pools[zone] = cx_Oracle.SessionPool(
                user="ONBOARDKL",
                password="Onboard_KL2025",
                dsn="10.190.8.95/SIMIMS",
                min=2, max=10, increment=1, threaded=True
            )

    return pools[zone]


def get_zone_from_circle(circle_code: int) -> str:
    mapping = {
        77: "EZ", 51: "SZ", 71: "EZ", 73: "EZ", 78: "EZ",
        40: "SZ", 3: "WZ", 2: "NZ", 10: "WZ", 61: "NZ",
        55: "NZ", 65: "NZ", 76: "EZ", 53: "SZ", 50: "SZ",
        4: "WZ", 1: "WZ", 74: "EZ", 75: "EZ", 72: "EZ",
        56: "NZ", 59: "NZ", 79: "EZ", 54: "SZ", 41: "SZ",
        60: "NZ", 62: "NZ", 64: "NZ", 70: "EZ"
    }
    return mapping.get(circle_code)

# views.py



@api_view(["POST"])
@permission_classes([IsAuthenticated])
def get_customer_info(request):

    serializer = CustomerInfoSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    gsm = serializer.validated_data["gsm"]
    circle = serializer.validated_data["circle"]
    req_type = serializer.validated_data["req_type"]

    zone = get_zone_from_circle(int(circle))
    if not zone:
        return Response(
            {"status": "failure", "message": "Invalid circle code"},
            status=status.HTTP_400_BAD_REQUEST
        )

    pool = get_pool(zone)

    conn = pool.acquire()
    try:
        record=get_bcd_details_by_gsm(gsm)
        records = [record] if record else []
        if not records:
            cursor = conn.cursor()
            out_cursor = cursor.var(cx_Oracle.CURSOR)

            cursor.callproc(
                "SIMMGMT.GSM_CUSTOMER_INFO_KERALA",
                [gsm, circle, req_type, out_cursor]
            )

            result_cursor = out_cursor.getvalue()
            columns = [col[0] for col in result_cursor.description]
            records = [dict(zip(columns, row)) for row in result_cursor]
        remarks = None
        allowed ="No"
        message=""
        if records:
            remarks = records[0].get("REMARKS")
            act_type = records[0].get("ACT_TYPE")
            act_type_upper = (act_type or "").upper()
            category=map_caf_type_to_category(remarks)
            if category:
                if category=="INDIVIDUAL":
                    allowed= "Yes"
                    message= "ALLOWED"
                elif category=="BULK":
                    allowed="No"
                    message="Bulk connections are not allowed, Please contact BSNL Customer Care."
            elif "EKYC" in act_type_upper:
                allowed="Yes"
                message= "ALLOWED"
            else:
                allowed="No"
                message= "Details remarks not available for migration, Please contact BSNL Customer Care."
        else:
            allowed="No"
            message= "Details remarks not available for migration, Please contact BSNL Customer Care." 

        return Response(
            {"status": "success","message": message,"allowed":allowed, "data": records},
            status=status.HTTP_200_OK
        )

    except cx_Oracle.DatabaseError as e:
        return Response(
            {"status": "error", "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    finally:
        pool.release(conn)

