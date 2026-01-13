import oracledb
from datetime import datetime
from ..models import CosBcd

def get_oracle_conn():
    return oracledb.connect(
        user="APPUSER1",
        password="W7b5NpQ8Z",
        dsn="10.201.222.66:1521/ecaf"
    )

def map_caf_type_to_category(caf_type: str, default="") -> str:
    """
    Maps CAF type to category (BULK / INDIVIDUAL)

    Example:
        map_caf_type_to_category("CUG") -> "BULK"
        map_caf_type_to_category("ekyc-post") -> "INDIVIDUAL"
    """

    if not caf_type:
        return default

    mapping = {
        "AUCTION": "INDIVIDUAL",
        "BULK": "BULK",
        "CMNP": "BULK",
        "CMNP-PRE": "BULK",
        "CUG": "BULK",
        "CUG-ADDON": "BULK",
        "CUG-CYMN": "BULK",
        "CYMN": "INDIVIDUAL",
        "DATACARD(EVDO,MICRO)": "INDIVIDUAL",
        "DEALER CAF": "INDIVIDUAL",
        "EKYC-AUCTION": "INDIVIDUAL",
        "EKYC-CYMN": "INDIVIDUAL",
        "EKYC-FANCY": "INDIVIDUAL",
        "EKYC-MNP": "INDIVIDUAL",
        "EKYC-NORMAL": "INDIVIDUAL",
        "EKYC-POST": "INDIVIDUAL",
        "EKYC-POST2PRE": "INDIVIDUAL",
        "EKYC-PRE2POST": "INDIVIDUAL",
        "EKYC-SIMSWAP": "INDIVIDUAL",
        "FANCY": "INDIVIDUAL",
        "INTERNET": "INDIVIDUAL",
        "MNP": "INDIVIDUAL",
        "MNP DEALER CAF": "INDIVIDUAL",
        "MOBILE-ECAF": "INDIVIDUAL",
        "NAME_SWAP": "INDIVIDUAL",
        "NORMAL": "INDIVIDUAL",
        "NUMBER BY CHOICE": "INDIVIDUAL",
        "PANTEL CAF": "INDIVIDUAL",
        "POST": "INDIVIDUAL",
        "POST_TO_PRE": "INDIVIDUAL",
        "POST2PRE": "INDIVIDUAL",
        "PRE TO POST": "INDIVIDUAL",
        "PRE2POST": "INDIVIDUAL",
        "PREPAID BY CHOICE": "INDIVIDUAL",
        "PREPAID NORMAL": "INDIVIDUAL",
        "PREPAID TO POSTPAID": "INDIVIDUAL",
        "REV-PRE": "INDIVIDUAL",
        "SERVICE": "INDIVIDUAL",
        "SIMSWAP": "INDIVIDUAL",
        "SIMSWAP_PREPAID": "INDIVIDUAL",
        "SUBMITTED BY CELLONEHYD": "INDIVIDUAL",
        "VENDOR CAF": "INDIVIDUAL",
        "VPN": "BULK",
        "VPN-ADDON": "BULK",
    }

    key = caf_type.strip().upper()
    return mapping.get(key, default)




def map_connection_type(value):
    if value == 1:
        return "PREPAID"
    if value == 2:
        return "POSTPAID"
    return None

def get_bcd_details_by_gsm(gsmnumber: str):
    """
    Fetch BCD details using GSM number and return in required response format
    """

    sql = """
        SELECT
            ACCOUNT_NO,
            NAME,
            TRIM(CAF_SERIAL_NO) AS CAF_SERIAL_NO,  -- Add TRIM here
            UID_NO,
            SIMNUMBER,
            PERM_ADDR_HNO,
            PERM_ADDR_STREET,
            PERM_ADDR_LOCALITY,
            PERM_ADDR_CITY,
            PERM_ADDR_STATE,
            PERM_ADDR_PIN,
            SSA_CODE,
            HLR_INIT_ACT_DATE,
            EMF_CONFIG_ID,
            CONNECTION_TYPE,
            ACT_TYPE
        FROM CAF_ADMIN.BCD
        WHERE GSMNUMBER = :gsmnumber 
        AND ACTIVATION_STATUS = 'C'
    """

    conn = get_oracle_conn()
    with conn.cursor() as cur:
        cur.execute(sql, gsmnumber=gsmnumber)
        row = cur.fetchone()
        if not row:
            return None
        columns = [col[0] for col in cur.description]
        record = dict(zip(columns, row))
    
    # Strip whitespace from CAF_SERIAL_NO in Python as well (defense in depth)
    caf_serial = record.get("CAF_SERIAL_NO")

    if caf_serial:
        caf_serial = caf_serial.strip()  # Remove any remaining whitespace
        record["CAF_SERIAL_NO"] = caf_serial
    
    # Determine ACT_TYPE
    if caf_serial and caf_serial.startswith("BE"):
        act_type = "EKYC"
    else:
        act_type = "DKYC"
    
    photo_id_sno = (
    CosBcd.objects
    .filter(caf_serial_no=caf_serial)
    .values_list('photo_id_sno', flat=True)
    .first()
    )

    last_4_digits = photo_id_sno[-4:] if photo_id_sno else None


    # Map DB → API response
    response = {
        "ACCOUNT_NO": record.get("ACCOUNT_NO"),
        "BILL_FNAME": record.get("NAME"),     
        "BILL_LNAME": None,
        "BILL_MINIT": None,

        "BILL_ADDRESS1": record.get("PERM_ADDR_HNO"),
        "BILL_ADDRESS2": record.get("PERM_ADDR_STREET"),
        "BILL_ADDRESS3": record.get("PERM_ADDR_LOCALITY"),

        "BILL_CITY": record.get("PERM_ADDR_CITY"),
        "BILL_STATE": record.get("PERM_ADDR_STATE"),
        "BILL_ZIP": record.get("PERM_ADDR_PIN"),

        "IN_ACTIVE_DATE": record.get("HLR_INIT_ACT_DATE"),
        "EMF_CONFIG_ID": record.get("EMF_CONFIG_ID"),

        "CONNECTION_TYPE": map_connection_type(record.get("CONNECTION_TYPE")),
        "UID_NO": last_4_digits,
        "CUSTOMER_UID_TOKEN": None,

        "ACT_TYPE": act_type,
        "ACC_BALANCE": 0,

        "SIMNUMBER": record.get("SIMNUMBER"),
        "AMOUNT_REQ": "YES",

        "CAF_SERIAL_NO": caf_serial,  # Use the trimmed value
        "SSA_CODE": record.get("SSA_CODE"),
        "REMARKS": "SSA_UPD_FRM_NULL"
    }

    return response