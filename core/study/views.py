from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Count, Subquery, OuterRef

from core.models import Study, StudyMember, StudyRole
from .serializers import (
    StudyCreateSerializer,
    StudyDetailSerializer,
    StudyUpdateSerializer,
    StudyJoinSerializer,
    StudyListSerializer,
)
from .services import StudyService, StudyMemberService
from .permissions import IsStudyOwner, IsStudyMember


class StudyCreateView(APIView):
    """스터디 생성 View"""

    permission_classes = [IsAuthenticated]
    service_class = StudyService

    def post(self, request):
        serializer = StudyCreateSerializer(data=request.data)
        if serializer.is_valid():
            service = self.service_class()
            study = service.create_study_with_owner(
                owner=request.user, validated_data=serializer.validated_data
            )

            return Response(
                StudyCreateSerializer(study).data, status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StudyDetailView(APIView):
    """스터디 상세 조회 및 수정 View"""

    permission_classes = [IsAuthenticated, IsStudyMember]

    def get_permissions(self):
        """HTTP 메서드에 따라 다른 권한 적용"""
        if self.request.method == "GET":
            return [IsAuthenticated(), IsStudyMember()]
        elif self.request.method == "PATCH":
            return [IsAuthenticated(), IsStudyOwner()]
        elif self.request.method == "DELETE":
            return [IsAuthenticated(), IsStudyOwner()]
        return [IsAuthenticated()]

    def get(self, request, id):
        """스터디 상세 조회"""
        # Subquery를 사용하여 현재 유저의 role을 'my_role'이라는 필드로 추가
        study = get_object_or_404(
            Study.objects.annotate(
                current_user_role=Subquery(
                    StudyMember.objects.filter(
                        study=OuterRef("pk"), user=request.user
                    ).values("role")[:1]
                )
            ),
            id=id,
        )

        serializer = StudyDetailSerializer(study, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, id):
        """스터디 수정"""
        study = get_object_or_404(Study, id=id)

        serializer = StudyUpdateSerializer(study, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        """스터디 삭제(스터디 장만 가능)"""
        study = get_object_or_404(Study, id=id)
        study.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class StudyJoinView(APIView):
    """스터디 가입 View"""

    permission_classes = [IsAuthenticated]
    service_class = StudyMemberService

    def post(self, request):
        serializer = StudyJoinSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        invite_code = serializer.validated_data["invite_code"]

        try:
            service = self.service_class()
            study = service.join_study(user=request.user, invite_code=invite_code)
        except ValueError as e:
            return Response(
                {
                    "error": {
                        "code": "ALREADY_MEMBER",
                        "message": str(e),
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "message": "스터디에 가입되었습니다.",
                "study_id": study.id,
            },
            status=status.HTTP_201_CREATED,
        )


class StudyLeaveView(APIView):
    """스터디 멤버의 스터디 탈퇴 View"""

    permission_classes = [IsAuthenticated, IsStudyMember]

    def delete(self, request, id):
        membership = get_object_or_404(StudyMember, study_id=id, user=request.user)

        if membership.role == StudyRole.OWNER:
            return Response(
                {
                    "error": {
                        "code": "OWNER_CANNOT_LEAVE",
                        "message": "스터디 오너는 탈퇴할 수 없습니다.",
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        membership.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class StudyListView(APIView):
    """가입한 스터디 목록 조회 View"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 현재 사용자가 가입한 스터디 목록 조회 (N+1 쿼리 방지를 위해 annotate 사용)
        study_memberships = (
            StudyMember.objects.filter(user=request.user)
            .select_related("study")
            .annotate(member_count=Count("study__members"))
        )

        serializer = StudyListSerializer(study_memberships, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
