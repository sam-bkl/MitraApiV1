import os
import random
import string
import requests
import json
from dotenv import load_dotenv, find_dotenv

# Load .env from /home/bsnlcos/cert_pyro
load_dotenv(find_dotenv())
class PyroUsimSimSaleApiClient:
    def __init__(self):
        self.api_url = self._get_env("PYRO_USIM_LOCAL_API_URL")
        self.ca_cert = self._get_env("PYRO_USIM_CA_CERT")
        self.client_cert = self._get_env("PYRO_USIM_CLIENT_CERT")
        self.client_key = self._get_env("PYRO_USIM_CLIENT_KEY")

    def _get_env(self, name):
        val = os.environ.get(name)
        if not val:
            raise Exception(f"Missing environment variable: {name}")
        return val

    def generate_transaction_id(self):
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choices(chars, k=12))

    def submit(self, request_data):
        transaction_id = self.generate_transaction_id()

        # Map request to wire format
        wire_request = {
            "simVendor": request_data.get("SimVendor"),
            "circleId": request_data.get("CircleId"),
            "msisdn": request_data.get("Msisdn"),
            "iccid": request_data.get("Iccid"),
            "brand": request_data.get("Brand"),
            "international": 1 if request_data.get("International") else 0,
            "simType": request_data.get("SimType"),
            "channelName": request_data.get("ChannelName"),
            "method_name": request_data.get("MethodName"),
            "transactionId": transaction_id
        }

        try:
            # Sending POST request with mTLS and CA verification
            response = requests.post(
                self.api_url,
                json=wire_request,
                verify=self.ca_cert,
                cert=(self.client_cert, self.client_key),
                timeout=30
            )

            # Print raw json as in the original C# implementation
            print(response.text)

            response_json = {}
            try:
                response_json = response.json()
            except:
                pass

            print("Got Root")
            # Using str(response_json) to mimic Console.WriteLine(root) which might output something like "{ ... }" or python dict repr
            print(response_json)

            return {
                "StatusCode": response.status_code,
                "Status": response_json.get("status", "FAILED"),
                "StatusDescription": response_json.get("statusDescription", ""),
                "Data": response_json.get("data"),
                "IsSuccess": response.status_code == 200
            }

        except Exception as e:
            raise e
