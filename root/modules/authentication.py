from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed

from root.settings import TOKEN_EXPIRY


def is_token_expired(token):
    expiration_time = token.created + TOKEN_EXPIRY
    return expiration_time < timezone.now()


class ExpiringTokenAuthentication(TokenAuthentication):
    def authenticate_credentials(self, key):
        print(True)
        try:
            token = Token.objects.get(key=key)
        except Token.DoesNotExist:
            raise AuthenticationFailed("Invalid token")

        if not token.user.is_active:
            raise AuthenticationFailed("User is inactive or deleted")

        expired = is_token_expired(token)
        if expired:
            raise AuthenticationFailed("Token has expired")

        return (token.user, token)
