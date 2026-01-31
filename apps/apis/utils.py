from django.utils import timezone
from datetime import date
from .hash_adh import hash_aadhaar
from .models import SimAllotmentAdh

def is_sim_allotted_today(aadhaar, circle_code):
    """
    Checks SIM allotment rules:
    - For all circles except 65: Only 1 SIM per day
    - For circle 65: Only 1 SIM every 10 days
    """

    aadhaar_hashed = hash_aadhaar(aadhaar)

    # Today's date
    today = timezone.now().date()

    qs = SimAllotmentAdh.objects.filter(aadhaar_hash=aadhaar_hashed)

    # -------- Rule 1: For circles except 65 → Only 1 SIM per day --------
    if circle_code != "65":
        if qs.filter(created_at__date=today).exists():
            allot = qs.filter(created_at__date=today).first()
            return True, allot.gsm_no     # SIM was already allotted today
        return False, None

    # -------- Rule 2: For circle 65 (Jammu Kashmir) → Only 1 SIM every 10 days --------
    last_allotment = qs.order_by('-created_at').first()

    if last_allotment:
        last_date = last_allotment.created_at.date()
        days_since = (today - last_date).days

        if days_since < 11:   # Restrict issuance
            return True, last_allotment.gsm_no

    return False, None

def insert_sim_allotment(aadhaar, gsm_no, circle_code):
    aadhaar_hashed = hash_aadhaar(aadhaar)

    SimAllotmentAdh.objects.create(
        aadhaar_hash=aadhaar_hashed,
        gsm_no=gsm_no,
        circle_code=circle_code,
        created_at=timezone.now()
    )

def get_client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    xri = request.META.get("HTTP_X_REAL_IP")
    ra = request.META.get("REMOTE_ADDR")

    if xff:
        return xff.split(",")[0].strip()
    if xri:
        return xri
    return ra

from django.utils import timezone

def safe_clone_instance(
    source_obj,
    target_model,
    *,
    exclude_fields=None,
    override_fields=None
):
    """
    Safely clone a model instance to another model.
    - BinaryField safe
    - No model_to_dict
    - No __dict__
    """

    exclude_fields = set(exclude_fields or [])
    override_fields = override_fields or {}

    data = {}

    for field in source_obj._meta.fields:
        field_name = field.name

        if field_name in exclude_fields:
            continue

        # Copy value directly (BinaryField safe)
        data[field_name] = getattr(source_obj, field_name)

    # Apply overrides (timestamps, status, etc.)
    data.update(override_fields)

    return target_model.objects.create(**data)
