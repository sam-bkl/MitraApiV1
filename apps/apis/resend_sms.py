import requests

url = "https://bulksms.bsnl.in:5010/api/Send_SMS"
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1bmlxdWVfbmFtZSI6IjEwMDIwIDMiLCJuYmYiOjE3NjI0MTkzMTEsImV4cCI6MTc5Mzk1NTMxMSwiaWF0IjoxNzYyNDE5MzExLCJpc3MiOiJodHRwczovL2J1bGtzbXMuYnNubC5pbjo1MDEwIiwiYXVkIjoiMTAwMjAgMyJ9.Onm5hbS2_k_BcueccKrNGoEDhi51U0dkqrxzHDUkyQY"

def resend_sms(number,otp,purpose="Login"):
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

    response = requests.post(url, json=payload, headers=headers,proxies=proxies,timeout=30)

    print("STATUS:", response.status_code)
    print("RESPONSE:", response.text)
    return

