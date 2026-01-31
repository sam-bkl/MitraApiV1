import os
import sys
import django
import requests
import urllib3
from pprint import pprint

# Disable SSL warnings if using verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Django setup
BASE_DIR = "/home/bsnlcos/apis"
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.conf import settings

# Config
URL = "https://m2mbsnlkerala.bsnl.co.in/api/SearchCustomerDetails/"
SEARCH_TEXT = "AMAL"

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
}

# Try without proxy first (since Postman works)
USE_PROXY = False  # Set to True if you need proxy

if USE_PROXY:
    PROXIES = getattr(settings, "PROXIES", None)
else:
    PROXIES = None

try:
    print("Calling M2M API")
    print("Using proxy:", PROXIES)

    response = requests.post(
        URL,
        params={"customer_name": SEARCH_TEXT},
        headers=HEADERS,
        proxies=PROXIES,
        timeout=(10, 30),  # (connect timeout, read timeout)
        verify=False  # Change to True once SSL is properly configured
    )

    print("HTTP STATUS:", response.status_code)
    print("RAW RESPONSE:")
    print(response.text)

    response.raise_for_status()

    print("\nPARSED JSON:")
    pprint(response.json())

except requests.exceptions.ProxyError as e:
    print("❌ Proxy error - try disabling proxy")
    print(e)

except requests.exceptions.SSLError as e:
    print("❌ SSL error - set verify=False or provide CA bundle")
    print(e)

except requests.exceptions.Timeout:
    print("❌ Timeout - check network/proxy configuration")

except requests.exceptions.HTTPError as e:
    print("❌ HTTP error")
    print(e)

except Exception as e:
    print("❌ Unexpected error")
    print(e)