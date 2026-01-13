from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.permissions import IsAuthenticated , AllowAny
from ..models import CtopMaster,Simprepaid, Simpostpaid, GsmChoice ,ApiOtpTable, AppVersion,RefOtpTable,CosBcd,FrcPlan
from ..serializers import CtopMasterSerializer,SimprepaidSerializer,SimpostpaidSerializer,GsmChoiceSerializer,AppVersionSerializer
import random
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.cache import cache
from django.utils import timezone
import requests,json
import time
from django.utils.timezone import now
from django.db import transaction
from django.db import connections

import psycopg2
from psycopg2 import pool

def get_pg_conn():
    return psycopg2.connect(
        database="postgres",
        user="postgres",
        password="1tc3llKL",
        host="10.201.222.67",
        port=5432
    )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_verification_status(request):
    try:
        username = request.data.get("ctopupno")
        status_param = request.data.get("caf_status")

        if not username or not status_param:
            return Response(
                {
                    "status": "failure",
                    "message": "username and status are required"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Map request status to database values
        status_mapping = {
            "caf_pending": None,
            "caf_active": "Y",
            "caf_activated": "ACTIVATED",  # New status for final activation
            "caf_rejected": "R",
            "caf_see_later": "F"
        }

        status_param = status_mapping.get(status_param, "INVALID")

        if status_param == "INVALID":
            return Response(
                {
                    "status": "failure",
                    "message": "Invalid status. Use caf_pending, caf_active, caf_activated, caf_rejected, or caf_see_later"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result_list = []
        conn = get_pg_conn()
        # Handle activated CAFs from second database
        if status_param == "ACTIVATED":
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        "HLR_FINAL_ACT_DATE", 
                        "CAF_SERIAL_NO", 
                        "REST"
                    FROM public.bcd_activation_completion_log
                    WHERE "REST"->>'DE_USERNAME' = %s
                """, [username])
                
                rows = cur.fetchall()
                for row in rows:
                    rest_data = row[2] if isinstance(row[2], dict) else json.loads(row[2] or '{}')
                    
                    item = {
                        "caf_id": row[1],
                        "mobileno": rest_data.get('gsmnumber'),
                        "simnumber": rest_data.get('simnumber'),
                        "caf_type": rest_data.get('caf_type'),
                        "category": "prepaid" if rest_data.get('connection_type') == 1 else "postpaid",
                        "time_act": row[0].isoformat() if row[0] else None,
                        "status": "activated",
                        "rejection_reason": ""
                    }
                    result_list.append(item)
        
        else:
            # Get activated CAF IDs to exclude from approved
            activated_caf_ids = set()
            if status_param == "Y":  # Only exclude if requesting approved CAFs
                with connections['activation_db'].cursor() as cursor:
                    cursor.execute("""
                        SELECT "CAF_SERIAL_NO" 
                        FROM public.bcd_activation_completion_log
                        WHERE "REST"->>'DE_USERNAME' = %s
                    """, [username])
                    activated_caf_ids = {row[0] for row in cursor.fetchall()}
            
            # Filter records from main database
            if status_param is None:
                records = CosBcd.objects.filter(
                    de_username=username,
                    verified_flag__isnull=True
                ) | CosBcd.objects.filter(
                    de_username=username,
                    verified_flag=""
                )
            else:
                records = CosBcd.objects.filter(
                    de_username=username,
                    verified_flag=status_param
                )
            
            # Exclude activated CAFs from approved list
            if status_param == "Y" and activated_caf_ids:
                records = records.exclude(caf_serial_no__in=activated_caf_ids)
            
            status_map = {
                "Y": "approved",
                "R": "rejected",
                "F": "see_later",
            }

            for rec in records:
                vf = (rec.verified_flag or "").upper().strip()
                status_value = status_map.get(vf, "pending")

                item = {
                    "caf_id": getattr(rec, "caf_serial_no", None),
                    "mobileno": rec.gsmnumber,
                    "simnumber": getattr(rec, "simnumber", None),
                    "caf_type": rec.caf_type,
                    "category": "prepaid" if getattr(rec, "connection_type", 1) == 1 else "postpaid",
                    "time_act": (
                        rec.verified_date.isoformat()
                        if getattr(rec, "verified_date", None)
                        else (
                            rec.live_photo_time.isoformat()
                            if getattr(rec, "live_photo_time", None)
                            else None
                        )
                    ),
                    "status": status_value,
                    "rejection_reason": getattr(rec, "rejection_reason", None) or ""
                }
                result_list.append(item)

        return Response(
            {
                "count": len(result_list),
                "records": result_list
            },
            status=status.HTTP_200_OK
        )

    except Exception as e:
        return Response(
            {"status": "failure", "message": f"Error: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )