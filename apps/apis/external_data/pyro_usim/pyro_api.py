import sys
from .PyroUsimSimSaleApiClient import PyroUsimSimSaleApiClient


def get_pyro_usim_imsi(gsmnumber, simnumber, circle_code, connection_type):
    """
    Fetch IMSI from Pyro USIM API

    connection_type:
        1 -> prepaid
        2 -> postpaid
    """

    try:
        client = PyroUsimSimSaleApiClient()

        sim_type = "Prepaid" if int(connection_type or 1) == 1 else "Postpaid"

        request = {
            "SimVendor": "IDEMIA",
            "CircleId": str(circle_code),
            "Msisdn": str(gsmnumber),
            "Iccid": str(simnumber),
            "Brand": "BSNL",
            "International": False,
            "SimType": sim_type,
            "ChannelName": "SancharAadhar",
            "MethodName": "NEW",
        }

        response = client.submit(request)

        # ---- Failure handling ----
        if not response.get("IsSuccess"):
            return {
                "success": False,
                "error": response.get("StatusDescription", "Pyro API failed"),
            }

        data = response.get("Data") or {}

        # ---- Success ----
        return {
            "success": True,
            "transaction_id": data.get("transactionId"),
            "imsi": data.get("imsi"),
            "msisdn": data.get("msisdn"),
            "iccid": data.get("iccid"),
            "pin1": data.get("pin1"),
            "puk1": data.get("puk1"),
            "pin2": data.get("pin2"),
            "puk2": data.get("puk2"),
        }

    except Exception as ex:
        return {
            "success": False,
            "error": str(ex),
        }


