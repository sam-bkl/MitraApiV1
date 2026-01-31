from ..models import CafSimSwapDetails
from django.utils import timezone
from rest_framework.response import Response
import base64, os
from datetime import datetime

def simswap_save(request, caf_id, ctopupno, actual_ip,mobileno):

    if "simswap_details" in request.data:
        simswap = request.data.get("simswap_details", {})
    elif "dkyc_simswap_details" in request.data:
        simswap = request.data.get("dkyc_simswap_details", {}) 

    #simswap = request.data.get("simswap_details", {})
    ss_list = simswap.get("simSwapDetailsFromSS", [])
    ss = ss_list[0] if isinstance(ss_list, list) and ss_list else {}

    # ------------------------------
    # Decode FIR base64 → bytes
    # ------------------------------
    fir_photo_base64 = simswap.get("firPhotoBase64")
    swap_reason = simswap.get("swapReason")
    mpin = simswap.get("mpin")
    
    fir_photo_path = None  # Initialize to None

    # FIR photo is required only for sim_lost
    if swap_reason == "sim_lost":
        if not fir_photo_base64:
            return Response(
                {"status": "failure", "message": "FIR photo required for lost SIM"},
                status=400
            )
        
        try:
            decoded_fir_photo = base64.b64decode(fir_photo_base64)
        except Exception as e:
            return Response(
                {"status": "failure", "message": f"Invalid base64 FIR photo: {str(e)}"},
                status=400
            )

        # ------------------------------
        # Save FIR photo to filesystem (ONLY for sim_lost)
        # ------------------------------
        today = datetime.now()
        base_dir = "/cosdata/files/cos_images/fir/"

        full_dir = os.path.join(base_dir, today.strftime("%Y"), today.strftime("%m"), today.strftime("%d"))
        os.makedirs(full_dir, exist_ok=True)

        fir_file_name = f"{caf_id}_fir.jpg"
        fir_photo_path = os.path.join(full_dir, fir_file_name)

        with open(fir_photo_path, "wb") as f:
            f.write(decoded_fir_photo)

    # ------------------------------
    # Parse date_of_lost if present
    # ------------------------------
    date_of_lost_value = simswap.get("dateOfLost")
    if date_of_lost_value:
        try:
            # Parse date string (assuming format like "2024-12-12" or "12/12/2024")
            if isinstance(date_of_lost_value, str):
                # Try different date formats
                for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]:
                    try:
                        date_of_lost_value = datetime.strptime(date_of_lost_value, fmt).date()
                        break
                    except ValueError:
                        continue
        except Exception:
            date_of_lost_value = None
    else:
        date_of_lost_value = None

    # ------------------------------
    # Convert ss_zip to string
    # ------------------------------
    ss_zip_value = ss.get("BILL_ZIP")
    if ss_zip_value is not None:
        ss_zip_value = str(ss_zip_value)

    # ------------------------------
    # Convert ss_acc_balance to proper type
    # ------------------------------
    ss_acc_balance_value = ss.get("ACC_BALANCE")
    if ss_acc_balance_value is not None:
        try:
            ss_acc_balance_value = float(ss_acc_balance_value)
        except (ValueError, TypeError):
            ss_acc_balance_value = None
    cir_code_cust=simswap.get("cir_code_pos")
    # ------------------------------
    # Now insert into DB
    # ------------------------------
    try:
        obj = CafSimSwapDetails(
            caf_id=caf_id,
            connection_type=ss.get("CONNECTION_TYPE"),  # From SS response
            swap_reason=swap_reason,
            circle=simswap.get("circle"),
            cir_code_pos=simswap.get("cir_code_pos"),
            mobile_number=mobileno,
            document_type=simswap.get("documentType"),
            act_type=simswap.get("actType"),

            # FIR details
            intimated_bsnl=simswap.get("intimatedBSNL"),
            date_of_lost=date_of_lost_value,
            fir_photo_path=fir_photo_path,  # Will be None if not sim_lost

            # Sanchaar Soft details
            ss_account_no=ss.get("ACCOUNT_NO"),
            ss_bill_fname=ss.get("BILL_FNAME"),
            ss_bill_lname=ss.get("BILL_LNAME"),
            ss_bill_minit=ss.get("BILL_MINIT"),
            ss_address1=ss.get("BILL_ADDRESS1"),
            ss_address2=ss.get("BILL_ADDRESS2"),
            ss_address3=ss.get("BILL_ADDRESS3"),
            ss_city=ss.get("BILL_CITY"),
            ss_state=ss.get("BILL_STATE"),
            ss_zip=ss_zip_value,  # Converted to string
            ss_in_active_date=ss.get("IN_ACTIVE_DATE"),
            ss_emf_config_id=ss.get("EMF_CONFIG_ID"),
            ss_connection_type=ss.get("CONNECTION_TYPE"),
            ss_uid_no=ss.get("UID_NO"),
            ss_customer_uid_token=ss.get("CUSTOMER_UID_TOKEN"),
            ss_act_type=ss.get("ACT_TYPE"),
            ss_acc_balance=ss_acc_balance_value,  # Converted to float
            ss_sim_number=ss.get("SIMNUMBER"),
            ss_amount_req=ss.get("AMOUNT_REQ"),
            ss_caf_serial_no=ss.get("CAF_SERIAL_NO"),
            ss_ssa_code=ss.get("SSA_CODE"),
            remarks = ss.get("REMARKS"),
            customer_type = ss.get("CUSTOMER_TYPE"),
            ss_group_id = ss.get("SS_GROUP_ID"),

            insert_user=ctopupno,
            ins_user_ip=actual_ip,
            insert_date=timezone.now(),
            mpin=mpin
        )

        obj.save()
        print(f"✓ SIM swap details saved successfully for CAF ID: {caf_id}")
        return {"status": "success","circle_code_cust":cir_code_cust, "message": "SIM swap details saved successfully"}
    except Exception as e:
        return {"status": "error", "message": f"Database error: {str(e)}"}