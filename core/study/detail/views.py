from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from core.models import Study
from .serializers import StudyDetailSerializer


class StudyDetailView(APIView):
    """스터디 상세 조회 View"""

    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        study = get_object_or_404(Study, id=id)
        serializer = StudyDetailSerializer(study)
        return Response(serializer.data, status=status.HTTP_200_OK)
