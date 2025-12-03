from django.db import IntegrityError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from core.utils.cookie import set_secure_cookie
from core.utils.cookie_lifetime import ACCESS_TOKEN_LIFETIME, REFRESH_TOKEN_LIFETIME
from .services import SocialLoginService


class SocialLoginView(APIView):
    service_class = SocialLoginService

    def post(self, request):
        provider = request.data.get("provider")
        access_token = request.data.get("access_token")
        service = self.service_class()

        try:
            user_data = service.fetch_user_info(provider, access_token)
            user, is_registration_required = service.login_or_create_user(
                provider, user_data
            )
        except ValueError as e:
            return Response(
                {
                    "error": {
                        "code": "INVALID_ACCESS_TOKEN",
                        "message": str(e),
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except IntegrityError:
            return Response(
                {
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "로그인 중 오류가 발생했습니다.",
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        is_registered = not is_registration_required

        response = Response(
            {
                "user": {
                    "id": user.id,
                    "provider": user.provider,
                    "email": user.email,
                    "username": user.username,
                    "boj_username": user.boj_username,
                    "profile_img_url": user.profile_img_url,
                },
                "is_registered": is_registered,
            },
            status=status.HTTP_200_OK,
        )

        set_secure_cookie(
            response,
            "access_token",
            access_token,
            max_age=ACCESS_TOKEN_LIFETIME,
        )
        set_secure_cookie(
            response,
            "refresh_token",
            refresh_token,
            max_age=REFRESH_TOKEN_LIFETIME,
        )
        set_secure_cookie(
            response,
            "is_registered",
            str(is_registered).lower(),
            max_age=REFRESH_TOKEN_LIFETIME,
        )

        return response
