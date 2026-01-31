import random
from django.utils import timezone
from datetime import timedelta
from requests.exceptions import RequestException
import logging
from ..create_cafid import get_sms_id
import requests

logger = logging.getLogger(__name__)

url = "https://osbmsg.cdr.bsnl.co.in/osb/EAINotificationService/EAISendNotificationRest"
brps_url = "https://bulksms.bsnl.in:5010/api/Send_SMS"
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1bmlxdWVfbmFtZSI6IjEwMDIwIDMiLCJuYmYiOjE3NjI0MTkzMTEsImV4cCI6MTc5Mzk1NTMxMSwiaWF0IjoxNzYyNDE5MzExLCJpc3MiOiJodHRwczovL2J1bGtzbXMuYnNubC5pbjo1MDEwIiwiYXVkIjoiMTAwMjAgMyJ9.Onm5hbS2_k_BcueccKrNGoEDhi51U0dkqrxzHDUkyQY"

def generate_otp():
    return str(random.randint(100000, 999999))

def choose_sms_gateway(is_resend: bool) -> str:
    if is_resend:
        return "BRPS"
    return "SDC"


def send_sms(number,otp,purpose,gateway):
    headers = {
    "Content-Type": "application/json"
    }
    trans_id = get_sms_id()
    #trans_id=101
    if gateway=='SDC':
        number = "0"+str(number)
        send_sms_sdc(number,otp,purpose)
    else:
        send_sms_brps(number,otp,purpose)
    return

def send_sms_sdc(number,otp,purpose):
    headers = {
    "Content-Type": "application/json"
    }
    trans_id = get_sms_id()
    number = "0"+str(number)
    payload = {
                    "TransactionId": trans_id,
                    "Environment": "Production",
                    "SourceProcess": "CRM",
                    "MessageType": "SMS",
                    "From": "BSNLSD",
                    "To": number,
                    "PE_ID": "1401643660000016974",
                    "TM_ID": "1407176509482415833",
                    "ZONE": "S",
                    "SSA": "CO",
                    "CIRCLE": "KL",
                    "MessageBody": f"{otp} is the OTP for {purpose} at BSNL COS.The OTP is valid for 10 minutes.Do not share with anyone."
                }
    try:
        response = requests.post(url, json=payload, headers=headers,timeout=(3, 5))
    except RequestException as e1:
        logger.warning(f"SDC sms unreachable failed: {e1}")
        try:
            response= send_sms_brps(number,otp,purpose)      
        except RequestException as e2:
            logger.error(f"BRPS failed: {e2}")
    return

def send_sms_brps(number,otp,purpose):
    headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
    }

    proxies = {
        "http": "http://10.198.216.107:3128",     # <-- replace with your proxy
        "https": "http://10.198.216.107:3128"     # <-- replace with your proxy
    }
    payload = {
    "Header": "BSNLMI",
    "Target": number,
    "Is_Unicode": "0",
    "Is_Flash": "0",
    "Message_Type": "SI",
    "Entity_Id": "1401601530000015602",
    "Content_Template_Id": "1407176483305773909",
    "Template_Keys_and_Values": [
        {"Key": "activity", "Value": purpose},
        {"Key": "otp", "Value": otp},
        {"Key": "subsystem", "Value": "COS"},
        {"Key": "validity", "Value": "10"},
        ]
    }
    try:
        response = requests.post(brps_url, json=payload, headers=headers,proxies=proxies,timeout=(3, 5))
    except RequestException as e1:
        logger.warning(f"BRPS sms unreachable failed: {e1}")
        try:
            response= send_sms_sdc(number,otp,purpose)
        except RequestException as e2:
            logger.error(f"SDC failed: {e2}")
    return
