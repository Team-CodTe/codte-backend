from django.db import IntegrityError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter

from core.models import User
from core.utils.cookie import (
    set_secure_cookie,
    ACCESS_TOKEN_LIFETIME,
    REFRESH_TOKEN_LIFETIME,
)
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

        response_data = {
            "user": {
                "id": user.id,
                "provider": user.provider,
                "email": user.email,
                "username": user.username,
                "boj_username": user.boj_username,
                "profile_img_url": user.profile_img_url,
            },
            "is_registered": is_registered,
        }
        serializer = SocialLoginResponseSerializer(data=response_data)
        serializer.is_valid(raise_exception=True)
        response = Response(serializer.validated_data, status=status.HTTP_200_OK)

        set_secure_cookie(
            response,
            "access_token",
            access_token,
            max_age=int(ACCESS_TOKEN_LIFETIME.total_seconds()),
        )
        set_secure_cookie(
            response,
            "refresh_token",
            refresh_token,
            max_age=int(REFRESH_TOKEN_LIFETIME.total_seconds()),
        )
        set_secure_cookie(
            response,
            "is_registered",
            str(is_registered).lower(),
            max_age=int(REFRESH_TOKEN_LIFETIME.total_seconds()),
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
            max_age=int(ACCESS_TOKEN_LIFETIME.total_seconds()),
        )
        set_secure_cookie(
            response,
            "refresh_token",
            new_refresh_token,
            max_age=int(REFRESH_TOKEN_LIFETIME.total_seconds()),
        )
        set_secure_cookie(
            response,
            "is_registered",
            str(is_registered).lower(),
            max_age=int(REFRESH_TOKEN_LIFETIME.total_seconds()),
        )
        return response


def _get_test_login_description():
    """테스트 로그인 API 설명을 동적으로 생성"""
    base_description = "테스트용으로 특정 유저 ID로 로그인합니다. (DEBUG 모드에서만 사용 가능)"
    
    try:
        users = User.objects.all().order_by('id')
        if users.exists():
            user_list = []
            for user in users:
                user_list.append(f"{user.username} : {user.id}")
            user_info = "\n\n사용 가능한 유저\n\n" + "\n\n".join(user_list)
            return base_description + user_info
    except Exception:
        # 데이터베이스 접근 실패 시 기본 설명만 반환
        pass
    
    return base_description


@extend_schema(tags=["auth"])
class TestLoginView(APIView):
    """테스트용 로그인 API (DEBUG 모드에서만 사용 가능)"""

    @extend_schema(
        summary="테스트 로그인",
        description=_get_test_login_description(),
        request=None,
        responses={
            200: SocialLoginResponseSerializer,
            400: ErrorEnvelopeSerializer,
            403: ErrorEnvelopeSerializer,
        },
        parameters=[
            OpenApiParameter(
                name="user_id",
                type=int,
                location=OpenApiParameter.QUERY,
                required=True,
                description="로그인할 유저 ID",
            )
        ],
    )
    def post(self, request):
        from django.conf import settings
        from datetime import timedelta

        # DEBUG 모드에서만 사용 가능
        if not settings.DEBUG:
            return Response(
                {
                    "error_code": "FORBIDDEN",
                    "message": "테스트 로그인은 DEBUG 모드에서만 사용할 수 있습니다.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response(
                {
                    "error_code": "MISSING_USER_ID",
                    "message": "user_id 파라미터가 필요합니다.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user_id = int(user_id)
        except ValueError:
            return Response(
                {
                    "error_code": "INVALID_USER_ID",
                    "message": "유효하지 않은 user_id입니다.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {
                    "error_code": "USER_NOT_FOUND",
                    "message": f"유저 ID {user_id}를 찾을 수 없습니다.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 만료되지 않는 토큰 생성 (100년 후 만료)
        test_token_lifetime = timedelta(days=36500)

        refresh = RefreshToken.for_user(user)
        access_token_obj = refresh.access_token
        access_token_obj.set_exp(from_time=None, lifetime=test_token_lifetime)

        access_token = str(access_token_obj)
        refresh_token = str(refresh)

        is_registered = bool(user.boj_username)

        response_data = {
            "user": {
                "id": user.id,
                "provider": user.provider,
                "email": user.email,
                "username": user.username,
                "boj_username": user.boj_username,
                "profile_img_url": user.profile_img_url,
            },
            "is_registered": is_registered,
        }
        serializer = SocialLoginResponseSerializer(data=response_data)
        serializer.is_valid(raise_exception=True)
        response = Response(serializer.validated_data, status=status.HTTP_200_OK)

        # 테스트용 access token 쿠키는 토큰 만료 시간과 동일하게 설정
        set_secure_cookie(
            response,
            "access_token",
            access_token,
            max_age=int(test_token_lifetime.total_seconds()),
        )
        set_secure_cookie(
            response,
            "refresh_token",
            refresh_token,
            max_age=int(REFRESH_TOKEN_LIFETIME.total_seconds()),
        )
        set_secure_cookie(
            response,
            "is_registered",
            str(is_registered).lower(),
            max_age=int(REFRESH_TOKEN_LIFETIME.total_seconds()),
        )

        return response
