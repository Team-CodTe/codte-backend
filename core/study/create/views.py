from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .serializers import StudyCreateSerializer


class StudyCreateView(APIView):
    """스터디 생성 View"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = StudyCreateSerializer(data=request.data)
        if serializer.is_valid():
            # owner는 현재 로그인한 사용자로 자동 설정
            study = serializer.save(owner=request.user)
            return Response(
                StudyCreateSerializer(study).data, status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
