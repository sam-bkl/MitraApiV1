import requests
from .create_cafid import get_sms_id

url = "https://osbmsg.cdr.bsnl.co.in/osb/EAINotificationService/EAISendNotificationRest"


def send_sms(number,otp):
    headers = {
    "Content-Type": "application/json"
    }
    trans_id = get_sms_id()
    trans_id=101
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
    response = requests.post(url, json=payload, headers=headers,timeout=30)
    return

def ref_send_sms(number,otp):
    headers = {
    "Content-Type": "application/json"
    }
    trans_id = get_sms_id()
    trans_id=101
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
    response = requests.post(url, json=payload, headers=headers,timeout=30)
    return

