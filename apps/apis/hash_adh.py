import hashlib
from django.conf import settings

FIXED_SALT = ")JwtkRW{V@PFvDBV&Wy}JnkA4nhV}m"   # or load from settings
PEPPER = settings.AADHAAR_PEPPER      # optional but recommended

def hash_aadhaar(aadhaar):
    data = aadhaar + FIXED_SALT + PEPPER
    return hashlib.sha256(data.encode()).hexdigest()