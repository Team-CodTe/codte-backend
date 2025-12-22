from django.db import IntegrityError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken
from drf_spectacular.utils import extend_schema, OpenApiExample

from core.models import User
from core.utils.cookie import set_secure_cookie
from core.utils.cookie_lifetime import ACCESS_TOKEN_LIFETIME, REFRESH_TOKEN_LIFETIME
from core.auth.services import SocialLoginService
from .serializers import (
    SocialLoginRequestSerializer,
    SocialLoginResponseSerializer,
)

from core.common.serializers import ErrorEnvelopeSerializer


@extend_schema(tags=["auth"])
class SocialLoginView(APIView):
    """소셜 로그인 API"""

    service_class = SocialLoginService

    @extend_schema(
        summary="소셜 로그인",
        description="OAuth provider의 access_token을 이용하여 로그인합니다.",
        request=SocialLoginRequestSerializer,
        responses={
            200: SocialLoginResponseSerializer,
            400: ErrorEnvelopeSerializer,
        },
        examples=[
            OpenApiExample(
                "성공 응답",
                value={
                    "user": {
                        "id": 1,
                        "provider": "google",
                        "email": "user@example.com",
                        "username": "user123",
                        "boj_username": "boj_user",
                        "profile_img_url": "https://example.com/profile.jpg",
                    },
                    "is_registered": True,
                },
                response_only=True,
            ),
        ],
    )
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
                    "error_code": "INVALID_ACCESS_TOKEN",
                    "message": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except IntegrityError:
            return Response(
                {
                    "error_code": "INTERNAL_SERVER_ERROR",
                    "message": "로그인 중 오류가 발생했습니다.",
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


@extend_schema(tags=["auth"])
class LogoutView(APIView):
    """로그아웃 API"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="로그아웃",
        description="현재 사용자를 로그아웃합니다. refresh_token을 블랙리스트에 추가하고 쿠키를 삭제합니다.",
        request=None,
        responses={
            204: None,
            401: ErrorEnvelopeSerializer,
        },
    )
    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except TokenError:
                return Response(
                    {
                        "error_code": "INVALID_REFRESH_TOKEN",
                        "message": "리프레시 토큰이 유효하지 않습니다.",
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )

        response = Response(status=status.HTTP_204_NO_CONTENT)

        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        response.delete_cookie("is_registered")

        return response


@extend_schema(tags=["auth"])
class TokenRefreshView(APIView):
    """토큰 갱신 API"""

    @extend_schema(
        summary="토큰 갱신",
        description="쿠키의 refresh_token을 이용하여 새로운 access_token과 refresh_token을 발급합니다.",
        request=None,
        responses={
            204: None,
            401: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
        },
    )
    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            return Response(
                {
                    "error_code": "REFRESH_TOKEN_NOT_FOUND",
                    "message": "리프레시 토큰이 존재하지 않습니다.",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = TokenRefreshSerializer(data={"refresh": refresh_token})

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError:
            return Response(
                {
                    "error_code": "REFRESH_TOKEN_INVALID",
                    "message": "리프레시 토큰이 유효하지 않습니다.",
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
                    "error_code": "USER_NOT_FOUND",
                    "message": "유저 정보를 찾을 수 없습니다.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        response = Response(status=status.HTTP_204_NO_CONTENT)

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
