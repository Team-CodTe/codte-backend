from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.exceptions import TokenError
from django.conf import settings


class TokenRefreshView(APIView):
    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            return Response(
                {
                    "error": {
                        "code": "REFRESH_TOKEN_NOT_FOUND",
                        "message": "리프레시 토큰이 존재하지 않습니다.",
                    }
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = TokenRefreshSerializer(data={"refresh": refresh_token})

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError:
            return Response(
                {
                    "error": {
                        "code": "REFRESH_TOKEN_INVALID",
                        "message": "리프레시 토큰이 유효하지 않습니다.",
                    }
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        new_access_token = serializer.validated_data["access"]
        new_refresh_token = serializer.validated_data.get("refresh", refresh_token)

        response = Response(status=status.HTTP_200_OK)

        cookie_kwargs = {
            "httponly": True,
            "samesite": "Lax",
            "secure": not settings.DEBUG,
        }

        response.set_cookie("access_token", new_access_token, **cookie_kwargs)
        response.set_cookie("refresh_token", new_refresh_token, **cookie_kwargs)

        return response
