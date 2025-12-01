from django.db import IntegrityError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings

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
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except IntegrityError:
            return Response(
                {"error": "로그인 중 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        response = Response(
            {
                "message": "로그인에 성공했습니다.",
                "user": {
                    "id": user.id,
                    "provider": user.provider,
                    "email": user.email,
                    "username": user.username,
                    "boj_username": user.boj_username,
                    "profile_img_url": user.profile_img_url,
                },
                "requires_registration": is_registration_required,
            },
            status=status.HTTP_200_OK,
        )

        cookie_kwargs = {
            "httponly": True,
            "samesite": "Lax",
            "secure": not settings.DEBUG,
        }

        response.set_cookie("access_token", access_token, **cookie_kwargs)
        response.set_cookie("refresh_token", refresh_token, **cookie_kwargs)

        return response
