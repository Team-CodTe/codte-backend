from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from core.utils.cookie import set_secure_cookie
from core.utils.cookie_lifetime import ACCESS_TOKEN_LIFETIME, REFRESH_TOKEN_LIFETIME
from django.contrib.auth import get_user_model

User = get_user_model()


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

        try:
            token_object = AccessToken(new_access_token)
            user_id = token_object["user_id"]
            user = User.objects.get(id=user_id)
            is_registered = bool(user.boj_username)
        except (KeyError, User.DoesNotExist):
            return Response(
                {
                    "error": {
                        "code": "USER_NOT_FOUND",
                        "message": "유저 정보를 찾을 수 없습니다.",
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        response = Response(status=status.HTTP_200_OK)

        set_secure_cookie(
            response,
            "access_token",
            new_access_token,
            max_age=ACCESS_TOKEN_LIFETIME,
        )
        set_secure_cookie(
            response,
            "refresh_token",
            new_refresh_token,
            max_age=REFRESH_TOKEN_LIFETIME,
        )
        set_secure_cookie(
            response,
            "is_registered",
            str(is_registered).lower(),
            max_age=REFRESH_TOKEN_LIFETIME,
        )
        return response
