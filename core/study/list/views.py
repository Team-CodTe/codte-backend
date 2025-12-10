from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from core.models import StudyMember
from .serializers import StudyListSerializer


class StudyListView(APIView):
    """가입한 스터디 목록 조회 View"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 현재 사용자가 가입한 스터디 목록 조회
        study_memberships = StudyMember.objects.filter(user=request.user).select_related(
            "study"
        )

        serializer = StudyListSerializer(study_memberships, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
