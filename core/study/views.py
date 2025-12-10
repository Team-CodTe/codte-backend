from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import IntegrityError

from core.models import Study, StudyMember, StudyRole
from .serializers import (
    StudyCreateSerializer,
    StudyDetailSerializer,
    StudyUpdateSerializer,
    StudyJoinSerializer,
    StudyListSerializer,
)


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


class StudyDetailView(APIView):
    """스터디 상세 조회 및 수정 View"""

    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        """스터디 상세 조회"""
        study = get_object_or_404(Study, id=id)
        
        # 스터디 멤버만 조회 가능
        if not StudyMember.objects.filter(study=study, user=request.user).exists():
            return Response(
                {"error": {"code": "PERMISSION_DENIED", "message": "스터디 멤버만 조회할 수 있습니다."}},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        serializer = StudyDetailSerializer(study)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, id):
        """스터디 수정"""
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
