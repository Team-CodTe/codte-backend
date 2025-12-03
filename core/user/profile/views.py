from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import UserSignUpSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from core.utils.cookie import set_secure_cookie
from core.utils.cookie_lifetime import ACCESS_TOKEN_LIFETIME, REFRESH_TOKEN_LIFETIME


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
