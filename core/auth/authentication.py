from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from drf_spectacular.extensions import OpenApiAuthenticationExtension

from core.utils.cookie import ACCESS_TOKEN_COOKIE


class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        raw_token = request.COOKIES.get(ACCESS_TOKEN_COOKIE)

        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
        except AuthenticationFailed:
            return None

        return self.get_user(validated_token), validated_token


class CustomJWTAuthenticationExtension(OpenApiAuthenticationExtension):
    target_class = "core.auth.authentication.CustomJWTAuthentication"
    name = "CustomJWTAuthentication"

    def get_security_definition(self, auto_schema):
        return {
            "type": "apiKey",
            "in": "cookie",
            "name": ACCESS_TOKEN_COOKIE,
        }
