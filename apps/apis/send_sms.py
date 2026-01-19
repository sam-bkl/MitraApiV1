import requests
from .create_cafid import get_sms_id
from .resend_sms import resend_sms
from requests.exceptions import RequestException
import logging

logger = logging.getLogger(__name__)

url = "https://osbmsg.cdr.bsnl.co.in/osb/EAINotificationService/EAISendNotificationRest"


def send_sms(number,otp):
    headers = {
    "Content-Type": "application/json"
    }
    trans_id = get_sms_id()
    #trans_id=101
    brps_number=number
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
                    "MessageBody": f"{otp} is the OTP for login at BSNL COS.The OTP is valid for 10 minutes.Do not share with anyone."
                }
    try:
        response = requests.post(url, json=payload, headers=headers,timeout=(3, 5))
    except RequestException as e1:
        logger.warning(f"SDC sms unreachable failed: {e1}")
        try:
            response= resend_sms(brps_number,otp,"Login")
            
        except RequestException as e2:
            logger.error(f"BRPS failed: {e2}")
    return

def ref_send_sms(number,otp):
    headers = {
    "Content-Type": "application/json"
    }
    trans_id = get_sms_id()
    brps_number=number
    #trans_id=101
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
                    "MessageBody": f"{otp} is the OTP for local reference at BSNL Sim Activation.The OTP is valid for 10 minutes.Do not share with anyone."
                }
    try:
        response = requests.post(url, json=payload, headers=headers,timeout=(3, 5))
    except RequestException as e1:
        logger.warning(f"SDC sms unreachable failed: {e1}")
        try:
            response= resend_sms(brps_number,otp,"local reference")
            
        except RequestException as e2:
            logger.error(f"BRPS failed: {e2}")
    return

def upg_send_sms(number,otp):
    headers = {
    "Content-Type": "application/json"
    }
    trans_id = get_sms_id()
    brps_number=number
    #trans_id=101
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
                    "MessageBody": f"{otp} is the OTP for Sim Upgradation at BSNL COS.The OTP is valid for 10 minutes.Do not share with anyone."
                }
    try:
        response = requests.post(url, json=payload, headers=headers,timeout=(3, 5))
    except RequestException as e1:
        logger.warning(f"SDC sms unreachable failed: {e1}")
        try:
            response= resend_sms(brps_number,otp,"Sim Upgradation")
            
        except RequestException as e2:
            logger.error(f"BRPS failed: {e2}")
    return

def dkyc_send_sms(number,sms_type,otp):
    headers = {
    "Content-Type": "application/json"
    }
    trans_id = get_sms_id()
    brps_number=number
    #trans_id=101
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
                    "MessageBody": f"{otp} is the OTP for {sms_type} at BSNL COS.The OTP is valid for 10 minutes.Do not share with anyone."
                }
    try:
        response = requests.post(url, json=payload, headers=headers,timeout=(3, 5))
    except RequestException as e1:
        logger.warning(f"SDC sms unreachable failed: {e1}")
        try:
            response= resend_sms(brps_number,otp,sms_type)
            
        except RequestException as e2:
            logger.error(f"BRPS failed: {e2}")
    return


