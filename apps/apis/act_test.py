from .models import CosBcd
from django.db.models import Q

def check_vrf_status(request):
    try:
        # ------------------------------------------------
        # 1️⃣ Read request payload
        # ------------------------------------------------
        username = "9495005457"
        caf_status = "caf_rejected"
        caf_status = caf_status.strip().lower()

        # ------------------------------------------------
        # 2️⃣ Validate caf_status
        # ------------------------------------------------
        allowed_statuses = {
            "caf_pending",
            "caf_active",
            "caf_rejected",
            "caf_see_later"
        }

        # ------------------------------------------------
        # 3️⃣ Build queryset (NO UNION, NO LEAKAGE)
        # ------------------------------------------------
        if caf_status == "caf_pending":
            # Pending = NULL or empty
            records = CosBcd.objects.filter(
                de_username=username
            ).filter(
                Q(verified_flag__isnull=True) | Q(verified_flag="")
            )

        elif caf_status == "caf_active":
            records = CosBcd.objects.filter(
                de_username=username,
                verified_flag="Y"
            )

        elif caf_status == "caf_rejected":
            records = CosBcd.objects.filter(
                de_username=username,
                verified_flag="R"
            )

        elif caf_status == "caf_see_later":
            records = CosBcd.objects.filter(
                de_username=username,
                verified_flag="F"
            )
        print(records)
        return
        # ------------------------------------------------
        # 4️⃣ Empty result handling
        # ------------------------------------------------
        if not records.exists():
            return Response(
                {
                    "count": 0,
                    "records": []
                },
                status=status.HTTP_200_OK
            )

        # ------------------------------------------------
        # 5️⃣ Build response
        # ------------------------------------------------
        status_map = {
            "Y": "approved",
            "R": "rejected",
            "F": "see_later"
        }

        result_list = []

        for rec in records:
            vf = (rec.verified_flag or "").strip().upper()

            item = {
                "caf_id": getattr(rec, "caf_serial_no", None),
                "mobileno": rec.gsmnumber,
                "simnumber": getattr(rec, "simnumber", None),
                "caf_type": rec.caf_type,
                "category": (
                    "prepaid"
                    if getattr(rec, "connection_type", 1) == 1
                    else "postpaid"
                ),
                "time_act": (
                    rec.verified_date.isoformat()
                    if rec.verified_date
                    else (
                        rec.live_photo_time.isoformat()
                        if rec.live_photo_time
                        else None
                    )
                ),
                "status": status_map.get(vf, "pending"),
                "rejection_reason": rec.rejection_reason or ""
            }

            result_list.append(item)

        # ------------------------------------------------
        # 6️⃣ Final response
        # ------------------------------------------------
        return Response(
            {
                "count": len(result_list),
                "records": result_list
            },
            status=status.HTTP_200_OK
        )

    except Exception as e:
        return Response(
            {
                "status": "failure",
                "message": f"Internal error: {str(e)}"
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

