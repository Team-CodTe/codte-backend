from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from core.models import Study
from .serializers import StudyUpdateSerializer


class StudyUpdateView(APIView):
    """스터디 수정 View"""

    permission_classes = [IsAuthenticated]

    def patch(self, request, id):
        study = get_object_or_404(Study, id=id)

        # owner만 수정 가능
        if study.owner != request.user:
            return Response(
                {"error": {"code": "PERMISSION_DENIED", "message": "스터디 소유자만 수정할 수 있습니다."}},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = StudyUpdateSerializer(study, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
