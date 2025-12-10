from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import IntegrityError

from core.models import Study, StudyMember, StudyRole
from .serializers import StudyJoinSerializer


class StudyJoinView(APIView):
    """스터디 가입 View"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = StudyJoinSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        invite_code = serializer.validated_data["invite_code"]

        # 초대 코드로 스터디 찾기
        study = get_object_or_404(Study, invite_code=invite_code)

        # 이미 멤버인지 확인
        if StudyMember.objects.filter(study=study, user=request.user).exists():
            return Response(
                {"error": {"code": "ALREADY_MEMBER", "message": "이미 가입된 스터디입니다."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 스터디 멤버로 추가
        try:
            StudyMember.objects.create(
                study=study,
                user=request.user,
                role=StudyRole.MEMBER,
            )
        except IntegrityError:
            return Response(
                {"error": {"code": "ALREADY_MEMBER", "message": "이미 가입된 스터디입니다."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "message": "스터디에 가입되었습니다.",
                "study_id": study.id,
            },
            status=status.HTTP_201_CREATED,
        )
