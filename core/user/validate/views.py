from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import (
    UsernameValidationSerializer,
    BojUsernameValidationSerializer,
)


class UsernameValidationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = UsernameValidationSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            return Response(
                {"message": "사용 가능한 닉네임입니다."}, status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BojUsernameValidationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BojUsernameValidationSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            return Response(
                {"message": "사용 가능한 백준 계정입니다."},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
