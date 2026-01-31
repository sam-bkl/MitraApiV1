from django.utils import timezone
from .models import RevEkycDetails
from django.utils.dateparse import parse_datetime


def rev_ekyc_save(request, rev_ekyc_details: dict, cafid):
    try:
        # ---- extract SS block safely ----
        ss_list = rev_ekyc_details.get("responseDetailsFromSS") or []
        ss = ss_list[0] if ss_list else {}

        record = RevEkycDetails.objects.create(
            # ---- core fields ----
            gsmnumber=rev_ekyc_details.get("gsmnumber"),
            new_caf_id=cafid,
            otp=rev_ekyc_details.get("otp"),

            verified_at=parse_datetime(rev_ekyc_details.get("verified_at"))
                if rev_ekyc_details.get("verified_at") else None,

            purpose=rev_ekyc_details.get("purpose"),
            mobile_no=rev_ekyc_details.get("mobile_no"),
            circle_code=rev_ekyc_details.get("circle_code"),
            sim_no=rev_ekyc_details.get("sim_no"),
            imsi_no=rev_ekyc_details.get("imsi_no"),
            caf_no=rev_ekyc_details.get("caf_no"),

            upload_date=parse_datetime(rev_ekyc_details.get("upload_date"))
                if rev_ekyc_details.get("upload_date") else None,

            no_request_from=rev_ekyc_details.get("no_request_from"),
            caf_type=rev_ekyc_details.get("caf_type"),

            # ---- SS mapped fields ----
            ss_account_no=ss.get("ACCOUNT_NO"),
            ss_bill_fname=ss.get("BILL_FNAME"),
            ss_bill_lname=ss.get("BILL_LNAME"),
            ss_bill_minit=ss.get("BILL_MINIT"),
            ss_address1=ss.get("BILL_ADDRESS1"),
            ss_address2=ss.get("BILL_ADDRESS2"),
            ss_address3=ss.get("BILL_ADDRESS3"),
            ss_city=ss.get("BILL_CITY"),
            ss_state=ss.get("BILL_STATE"),
            ss_zip=str(ss.get("BILL_ZIP")) if ss.get("BILL_ZIP") else None,

            ss_in_active_date=parse_datetime(ss.get("IN_ACTIVE_DATE"))
                if ss.get("IN_ACTIVE_DATE") else None,

            ss_emf_config_id=ss.get("EMF_CONFIG_ID"),
            ss_connection_type=ss.get("CONNECTION_TYPE"),
            ss_uid_no=ss.get("UID_NO"),
            ss_customer_uid_token=ss.get("CUSTOMER_UID_TOKEN"),
            ss_act_type=ss.get("ACT_TYPE"),
            ss_acc_balance=ss.get("ACC_BALANCE"),
            ss_sim_number=ss.get("SIMNUMBER"),
            ss_amount_req=ss.get("AMOUNT_REQ"),
            ss_caf_serial_no=ss.get("CAF_SERIAL_NO"),
            ss_ssa_code=ss.get("SSA_CODE"),

            remarks=ss.get("REMARKS"),
            customer_type=ss.get("CUSTOMER_TYPE"),
            ss_group_id=ss.get("SS_GROUP_ID"),

            # ---- audit ----
            insert_username=getattr(request.user, "username"),
            insert_time=timezone.now(),
        )

        return {
            "status": "success",
            "circle_code_cust": rev_ekyc_details.get("circle_code"),
            "id": record.id
        }

    except Exception as e:
        return {
            "status": "failure",
            "message": str(e)
        }