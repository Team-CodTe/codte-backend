from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from core.utils.cookie import set_secure_cookie
from core.utils.cookie_lifetime import ACCESS_TOKEN_LIFETIME, REFRESH_TOKEN_LIFETIME
from .serializers import (
    UserInfoSerializer,
    UserSignUpSerializer,
    UsernameValidationSerializer,
    BojUsernameValidationSerializer,
)


class UserMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserInfoSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RegisterProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user

        serializer = UserSignUpSerializer(
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
                {"userId": user.id},
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


class UsernameValidationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = UsernameValidationSerializer(
            data=request.data,
            context={"request": request},
        )

        if serializer.is_valid():
            return Response(status=status.HTTP_200_OK)

        first_key = next(iter(serializer.errors))
        error_message = serializer.errors[first_key][0]

        return Response(
            {"message": error_message},
            status=status.HTTP_400_BAD_REQUEST,
        )


class BojUsernameValidationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BojUsernameValidationSerializer(
            data=request.data,
            context={"request": request},
        )

        if serializer.is_valid():
            return Response(status=status.HTTP_200_OK)

        first_key = next(iter(serializer.errors))
        error_message = serializer.errors[first_key][0]

        return Response(
            {"message": error_message},
            status=status.HTTP_400_BAD_REQUEST,
        )
