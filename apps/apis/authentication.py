from rest_framework.authentication import BaseAuthentication
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.exceptions import AuthenticationFailed

from apps.apis.models import CtopMaster


class CtopJWTAuthentication(BaseAuthentication):
    """
    Custom authentication that:
    - Reads JWT from Authorization header
    - Extracts ctopupno from token
    - Loads CtopMaster instead of Django User
    """

    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith("Bearer "):
            return None  # No authentication provided → let DRF handle it

        token_str = auth_header.split(" ")[1]

        try:
            token = AccessToken(token_str)
        except Exception:
            raise AuthenticationFailed("Invalid or expired token")

        # Extract identity
        ctopupno = token.get("ctopupno", None)

        if not ctopupno:
            raise AuthenticationFailed("Token missing ctopupno")

        # Load CtopMaster
        try:
            user = CtopMaster.objects.get(ctopupno=ctopupno)
        except CtopMaster.DoesNotExist:
            raise AuthenticationFailed("User not found")

        return (user, None)  # DRF expects a (user, auth) tuple
