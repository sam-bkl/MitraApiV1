from ..models import CosBcd
from django.db import transaction
from datetime import datetime, time
from django.utils import timezone
from django.db import transaction
from rest_framework.response import Response
from rest_framework import status as http_status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

import oracledb

def get_oracle_conn():
    return oracledb.connect(
        user="APPUSER1",
        password="W7b5NpQ8Z",
        dsn="10.201.222.66:1521/ecaf"
    )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_final_act_status(request):
    """
    Expected POST:
    {
            "caf_id": "BEC0044869",
            "mobileno": "9999999999",
            "simnumber": "987465213221",
            "caf_type": "cymn",
            "category": "prepaid",
            "time_act": "2025-12-13T11:38:28.270775+00:00",
            "status": "rejected",
            "rejection_reason": "test"
        }
    """
    
    conn = get_oracle_conn()
    caf_id = request.data.get("caf_id")
    mobileno = request.data.get("mobileno")
    simnumber = request.data.get("simnumber")
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT ACTIVATION_STATUS, ACTIVATION_REMARKS
                FROM CAF_ADMIN.BCD
                WHERE GSMNUMBER = :gsm
                AND CAF_SERIAL_NO = :caf
            """, gsm=mobileno, caf=caf_id)
            result = cur.fetchone()
    finally:
        conn.close()
    
    if not result:
        return Response(
            {"status": "not_found", "message": "No record found"},
            status=200
        )

    return Response(
        {
            "status": "success",
            "activation_status": result[0],
            "activation_remarks": result[1]
        },
        status=200
    )
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def edit_mnp(request):
    caf_id = request.data.get("caf_id")
    mobileno = request.data.get("mobileno")
    status_value = request.data.get("status")
    upc_code = request.data.get("upc_code")
    upc_code_validupto = request.data.get("upc_code_validupto")

    # ---------------- BASIC VALIDATION ----------------
    if not all([caf_id, mobileno, status_value, upc_code, upc_code_validupto]):
        return Response(
            {"status": "failure", "message": "Missing required fields"},
            status=http_status.HTTP_400_BAD_REQUEST
        )

    # ---------------- PARSE TIMESTAMPTZ ----------------
    # try:
    #     dt = datetime.strptime(upc_code_validupto, "%d/%m/%Y")
    #     upc_valid_upto = timezone.make_aware(
    #         datetime.combine(dt.date(), time(23, 59, 59))
    #     )
    # except ValueError:
    #     return Response(
    #         {
    #             "status": "failure",
    #             "message": "Invalid upc_code_validupto format (DD/MM/YYYY)"
    #         },
    #         status=http_status.HTTP_400_BAD_REQUEST
    #     )

    # ---------------- PENDING ----------------
    if status_value == "pending":
        record = CosBcd.objects.filter(
            gsmnumber=mobileno,
            caf_serial_no=caf_id
        ).first()

        if not record:
            return Response(
                {"status": "failure", "message": "CAF not found"},
                status=http_status.HTTP_404_NOT_FOUND
            )

        if record.verified_flag in (None, '', 'N'):
            record.upc_code = upc_code
            record.upcvalidupto = upc_code_validupto
            record.save(update_fields=["upc_code", "upcvalidupto"])

        return Response({"status": "success" , "data":{"upc_code":upc_code,"upcvalidupto":upc_code_validupto }}, status=http_status.HTTP_200_OK)

    # ---------------- CONFIRMED ----------------
    elif status_value == "approved":
        # 1️⃣ ORACLE FIRST
        conn = get_oracle_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE CAF_ADMIN.BCD
                    SET UPC_CODE = :upc,
                        ACTIVATION_STATUS = 'AI',
                        ACTIVATION_REMARKS  = NULL,
                        BILLING_STATUS      = NULL
                    WHERE GSMNUMBER = :gsm
                      AND CAF_SERIAL_NO = :caf
                      AND ACTIVATION_STATUS = 'R'
                """, {
                    "upc": upc_code,
                    "gsm": mobileno,
                    "caf": caf_id
                })

                # if cur.rowcount != 1:
                #     raise Exception("Oracle update failed or multiple rows affected")

            conn.commit()
        except Exception as e:
            conn.rollback()
            return Response(
                {"status": "failure", "message": str(e)},
                status=http_status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            conn.close()

        # 2️⃣ POSTGRES ATOMIC
        with transaction.atomic():
            record = (
                CosBcd.objects
                .filter(gsmnumber=mobileno, caf_serial_no=caf_id)
                .first()
            )

            if not record:
                return Response(
                    {"status": "failure", "message": "CAF not found in COS"},
                    status=http_status.HTTP_404_NOT_FOUND
                )

            if record.verified_flag == 'Y':
                record.upc_code = upc_code
                record.upcvalidupto = upc_code_validupto
                record.save(update_fields=["upc_code", "upcvalidupto"])

        return Response({"status": "success"}, status=http_status.HTTP_200_OK)

    # ---------------- INVALID STATUS ----------------
    return Response(
        {"status": "failure", "message": "Invalid status value"},
        status=http_status.HTTP_400_BAD_REQUEST
    )