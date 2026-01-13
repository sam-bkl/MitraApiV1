from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.forms.models import model_to_dict
from ..models import Simpostpaid,SimpostpaidSold,Simprepaid,SimprepaidSold,GsmChoice,GsmChoiceSold
from django.db import transaction

@transaction.atomic(using='legacy')
def update_inventory_atomic(simno, gsmno, connection_type, plan):
    """
    Atomic SIM + GSM inventory update
    connection_type: 1 = prepaid, 2 = postpaid
    plan: normal / mnp / simswap
    
    NOTE: Must be called within an existing transaction.atomic() block
    """
    
    # =====================================================
    # 1️⃣ SIM HANDLING
    # =====================================================
    if connection_type == 1:  # PREPAID

        # Already sold?
        if SimprepaidSold.objects.filter(simno=simno).exists():
            raise ValidationError(f"Prepaid SIM already sold: {simno}")

        # Lock SIM
        sim = (
            Simprepaid.objects
            .select_for_update()
            .filter(simno=simno)
            .first()
        )

        if not sim:
            raise ValidationError(f"Prepaid SIM not found: {simno}")

        # Move SIM → sold
        data = model_to_dict(sim)
        data["changed_date"] = timezone.now()

        SimprepaidSold.objects.create(**data)
        sim.delete()

    else:  # POSTPAID

        if SimpostpaidSold.objects.filter(simno=simno).exists():
            raise ValidationError(f"Postpaid SIM already sold: {simno}")

        sim = (
            Simpostpaid.objects
            .select_for_update()
            .filter(simno=simno)
            .first()
        )

        if not sim:
            raise ValidationError(f"Postpaid SIM not found: {simno}")
        
        data = model_to_dict(sim)
        data["changed_date"] = timezone.now()

        SimpostpaidSold.objects.create(**data)
        sim.delete()

    # =====================================================
    # 2️⃣ GSM HANDLING (skip for MNP / SIMSWAP)
    # =====================================================
    if plan not in ("mnp", "simswap","simupgrade"):

        if GsmChoiceSold.objects.filter(gsmno=gsmno).exists():
            raise ValidationError(f"GSM already sold: {gsmno}")

        gsm = (
            GsmChoice.objects
            .select_for_update()
            .filter(gsmno=gsmno)
            .first()
        )

        if not gsm:
            raise ValidationError(f"GSM not found: {gsmno}")
        
        data = model_to_dict(gsm)
        data["trans_date"] = timezone.now()

        GsmChoiceSold.objects.create(**data)
        gsm.delete()