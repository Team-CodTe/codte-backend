from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema

from core.utils.cookie import (
    set_secure_cookie,
    ACCESS_TOKEN_LIFETIME,
    REFRESH_TOKEN_LIFETIME,
)
from .serializers import (
    UserInfoSerializer,
    UserProfileSerializer,
    UserProfileErrorSerializer,
    UsernameValidationSerializer,
    BojUsernameValidationSerializer,
)
from core.common.serializers import ErrorEnvelopeSerializer


@extend_schema(tags=["user"])
class UserMeView(APIView):
    """현재 로그인한 사용자 정보 조회 API"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="내 정보 조회",
        description="현재 로그인한 사용자의 정보를 조회합니다.",
        responses={200: UserInfoSerializer},
    )
    def get(self, request):
        serializer = UserInfoSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(tags=["user"])
class UserProfileView(APIView):
    """사용자 프로필 관리 API"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="사용자 프로필 등록 및 수정",
        description="사용자의 username과 boj_username을 등록 및 수정합니다.",
        request=UserProfileSerializer,
        responses={
            200: UserInfoSerializer,
            400: UserProfileErrorSerializer,
        },
    )
    def patch(self, request):
        user = request.user

        serializer = UserProfileSerializer(
            user,
            data=request.data,
            context={"request": request},
            partial=True,
        )

        if serializer.is_valid():
            serializer.save()

            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            response = Response(
                UserInfoSerializer(user).data,
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
                "true",
                max_age=REFRESH_TOKEN_LIFETIME,
            )

            return response

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


@extend_schema(tags=["user"])
class UsernameValidationView(APIView):
    """사용자명 유효성 검사 API"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="사용자명 유효성 검사",
        description="입력한 username이 사용 가능한지 검사합니다. 중복 여부 및 형식을 확인합니다.",
        request=UsernameValidationSerializer,
        responses={
            204: None,
            400: ErrorEnvelopeSerializer,
        },
    )
    def post(self, request):
        serializer = UsernameValidationSerializer(
            data=request.data,
            context={"request": request},
        )

        if serializer.is_valid():
            return Response(status=status.HTTP_204_NO_CONTENT)

        first_key = next(iter(serializer.errors))
        error_message = serializer.errors[first_key][0]

        return Response(
            {
                "error_code": "INVALID_USERNAME",
                "message": error_message,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


@extend_schema(tags=["user"])
class BojUsernameValidationView(APIView):
    """백준 아이디 유효성 검사 API"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="백준 아이디 유효성 검사",
        description="입력한 boj_username이 사용 가능한지 검사합니다. 실제 백준 계정 존재 여부 및 중복을 확인합니다.",
        request=BojUsernameValidationSerializer,
        responses={
            204: None,
            400: ErrorEnvelopeSerializer,
        },
    )
    def post(self, request):
        serializer = BojUsernameValidationSerializer(
            data=request.data,
            context={"request": request},
        )

        if serializer.is_valid():
            return Response(status=status.HTTP_204_NO_CONTENT)

        first_key = next(iter(serializer.errors))
        error_message = serializer.errors[first_key][0]

        return Response(
            {
                "error_code": "INVALID_BOJ_USERNAME",
                "message": error_message,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
