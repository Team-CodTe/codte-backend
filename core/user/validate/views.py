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
