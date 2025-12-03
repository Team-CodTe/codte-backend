from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except TokenError:
                return Response(
                    {
                        "error": {
                            "code": "INVALID_REFRESH_TOKEN",
                            "message": "리프레시 토큰이 유효하지 않습니다.",
                        }
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )

        response = Response(status=status.HTTP_200_OK)

        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        response.delete_cookie("is_registered")

        return response
