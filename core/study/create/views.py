from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from core.models import StudyMember, StudyRole
from .serializers import StudyCreateSerializer


class StudyCreateView(APIView):
    """스터디 생성 View"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = StudyCreateSerializer(data=request.data)
        if serializer.is_valid():
            # owner는 현재 로그인한 사용자로 자동 설정
            study = serializer.save(owner=request.user)
            
            # 스터디 생성 시 owner를 StudyMember에 추가
            StudyMember.objects.create(
                study=study,
                user=request.user,
                role=StudyRole.OWNER,
            )
            
            return Response(
                StudyCreateSerializer(study).data, status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
