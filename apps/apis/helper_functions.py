from .models import CosBcd

def check_gsm_caf_logic(gsmno, caf_type):
    """
    Core CAF check logic.
    Can be reused by APIs, background jobs, scripts.
    """

    records = CosBcd.objects.filter(gsmnumber=gsmno)

    # Case 1: No CAF at all
    if not records.exists():
        return {
            "Allow": "Yes",
            "Reason": "No existing CAF found"
        }
    verified_record_swap = records.filter(
        caf_type="simswap",
        verified_flag='Y'
    ).order_by('-verified_date').first()

    if verified_record_swap:
        return {
            "Allow": "Yes",
            "Reason": "Sim swap CAF already exists and verified",
            "verified_date": verified_record_swap.verified_date
        }
    # Case 2: Verified CAF exists for same caf_type
    verified_record = (
        records
        .filter(caf_type=caf_type, verified_flag='Y')
        .order_by('-verified_date')
        .first()
    )

    if verified_record:
        return {
            "Allow": "No",
            "Reason": "CAF already exists and verified",
            "verified_date": verified_record.verified_date
        }

    # Case 3: CAF exists but pending verification
    pending_record = (
        records
        .filter(caf_type=caf_type, verified_flag__isnull=True)
        .order_by('-live_photo_time')
        .first()
    )

    if pending_record:
        return {
            "Allow": "No",
            "Reason": "CAF already exists and pending verification"
        }

    # Case 4: CAF exists for different caf_type
    other_record = (
        records
        .exclude(caf_type=caf_type)
        .order_by('-live_photo_time')
        .first()
    )

    if other_record:
        return {
            "Allow": "Yes",
            "Reason": "CAF exists for different caf_type",
            "existing_caf_type": other_record.caf_type
        }

    # Fallback
    return {
        "Allow": "Yes",
        "Reason": "CAF exists, CAF rejected"
    }
