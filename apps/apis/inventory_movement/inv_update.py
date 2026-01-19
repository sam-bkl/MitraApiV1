from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.forms.models import model_to_dict
from ..models import Simpostpaid,SimpostpaidSold,Simprepaid,SimprepaidSold,GsmChoice,GsmChoiceSold
from django.db import transaction
from ..esim.models import Esimpostpaid, Esimprepaid, EsimpostpaidSold, EsimprepaidSold

@transaction.atomic(using="legacy")
def update_inventory_atomic(simno, gsmno, connection_type, plan, sim_mode="physical"):
    """
    Atomic SIM + GSM inventory update

    connection_type:
        1 = prepaid
        2 = postpaid

    sim_mode:
        "physical" | "esim"

    plan:
        normal / mnp / simswap / simupgrade
    """

    # =====================================================
    # 1️⃣ SIM / eSIM HANDLING
    # =====================================================

    if sim_mode == "esim":

        # =========================
        # eSIM – PREPAID
        # =========================
        if connection_type == 1:

            if EsimprepaidSold.objects.filter(simno=simno).exists():
                raise ValidationError(f"eSIM already sold: {simno}")

            esim = (
                Esimprepaid.objects
                .select_for_update()
                .filter(simno=simno)
                .first()
            )

            if not esim:
                raise ValidationError(f"eSIM not found: {simno}")

            if esim.status != 2:
                raise ValidationError(
                    f"eSIM not in RESERVED state (status=2): {simno}"
                )

            EsimprepaidSold.objects.create(
                simno=esim.simno,
                imsi=esim.imsi,
                pukno1=esim.pukno1,
                pukno2=esim.pukno2,
                pin1=esim.pin1,
                pin2=esim.pin2,
                status=3,  # SOLD
                circle_code=esim.circle_code,
                changed_date=timezone.now(),
                qr_code=esim.qr_code,   
                dual_imsi=esim.dual_imsi,
                file_id=esim.file_id,
                plan_code=esim.plan_code,
            )

            esim.delete()

        # =========================
        # eSIM – POSTPAID
        # =========================
        else:

            if EsimpostpaidSold.objects.filter(simno=simno).exists():
                raise ValidationError(f"eSIM already sold: {simno}")

            esim = (
                Esimpostpaid.objects
                .select_for_update()
                .filter(simno=simno)
                .first()
            )

            if not esim:
                raise ValidationError(f"eSIM not found: {simno}")

            if esim.status != 2:
                raise ValidationError(
                    f"eSIM not in RESERVED state (status=2): {simno}"
                )

            EsimpostpaidSold.objects.create(
                simno=esim.simno,
                imsi=esim.imsi,
                pukno1=esim.pukno1,
                pukno2=esim.pukno2,
                pin1=esim.pin1,
                pin2=esim.pin2,
                status=3,  # SOLD
                circle_code=esim.circle_code,
                changed_date=timezone.now(),
                qr_code=esim.qr_code,   
                dual_imsi=esim.dual_imsi,
                file_id=esim.file_id,
                plan_code=esim.plan_code,
            )
            esim.delete()

    # =====================================================
    # 2️⃣ PHYSICAL SIM HANDLING (existing logic)
    # =====================================================
    else:

        if connection_type == 1:  # PREPAID

            if SimprepaidSold.objects.filter(simno=simno).exists():
                raise ValidationError(f"Prepaid SIM already sold: {simno}")

            sim = (
                Simprepaid.objects
                .select_for_update()
                .filter(simno=simno)
                .first()
            )

            if not sim:
                raise ValidationError(f"Prepaid SIM not found: {simno}")

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
    # 3️⃣ GSM HANDLING (unchanged)
    # =====================================================
    if plan not in ("mnp", "simswap", "simupgrade","cug"):

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
