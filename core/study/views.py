from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Count, Subquery, OuterRef
from drf_spectacular.utils import extend_schema, extend_schema_view

from core.models import Study, StudyMember, StudyRole
from .serializers import (
    DailyAssignmentListResponseSerializer,
    DailyAssignmentSerializer,
    ForceRefreshErrorSerializer,
    StudyCreateSerializer,
    StudyCreateErrorSerializer,
    StudyDetailSerializer,
    StudyUpdateSerializer,
    StudyJoinSerializer,
    StudyJoinResponseSerializer,
    StudyListSerializer,
)
from core.common.serializers import ErrorEnvelopeSerializer
from .services import (
    StudyService,
    StudyMemberService,
    DailyAssignmentService,
    RefreshCooldownError,
)
from .permissions import IsStudyOwner, IsStudyMember


@extend_schema(tags=["studies"])
class StudyCreateView(APIView):
    """스터디 생성 API"""

    permission_classes = [IsAuthenticated]
    service_class = StudyService

    @extend_schema(
        summary="스터디 생성",
        description="새로운 스터디를 생성합니다. 생성자는 자동으로 스터디장이 됩니다.",
        request=StudyCreateSerializer,
        responses={
            201: StudyCreateSerializer,
            400: StudyCreateErrorSerializer,
        },
    )
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


@extend_schema(tags=["studies"])
class StudyDetailView(APIView):
    """스터디 상세 조회, 수정, 삭제 API"""

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

    @extend_schema(
        summary="스터디 상세 조회",
        description="스터디의 상세 정보를 조회합니다. 스터디 멤버만 조회 가능합니다.",
        responses={200: StudyDetailSerializer},
    )
    def get(self, request, study_id):
        study = get_object_or_404(
            Study.objects.annotate(
                current_user_role=Subquery(
                    StudyMember.objects.filter(
                        study=OuterRef("pk"), user=request.user
                    ).values("role")[:1]
                )
            ),
            id=study_id,
        )

        self.check_object_permissions(request, study)

        serializer = StudyDetailSerializer(study, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="스터디 정보 수정",
        description="스터디 정보를 수정합니다. 스터디장만 수정 가능합니다.",
        request=StudyUpdateSerializer,
        responses={200: StudyUpdateSerializer},
    )
    def patch(self, request, study_id):
        study = get_object_or_404(Study, id=study_id)

        self.check_object_permissions(request, study)

        serializer = StudyUpdateSerializer(study, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="스터디 삭제",
        description="스터디를 삭제합니다. 스터디장만 삭제 가능합니다.",
        responses={204: None},
    )
    def delete(self, request, study_id):
        study = get_object_or_404(Study, id=study_id)

        self.check_object_permissions(request, study)

        study.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["studies"])
class StudyJoinView(APIView):
    """스터디 가입 API"""

    permission_classes = [IsAuthenticated]
    service_class = StudyMemberService

    @extend_schema(
        summary="스터디 가입",
        description="초대 코드를 이용하여 스터디에 가입합니다.",
        request=StudyJoinSerializer,
        responses={
            201: StudyJoinResponseSerializer,
            400: ErrorEnvelopeSerializer,
        },
    )
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
                    "error_code": "ALREADY_MEMBER",
                    "message": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "id": study.id,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["studies"])
class StudyLeaveView(APIView):
    """스터디 탈퇴 API"""

    permission_classes = [IsAuthenticated, IsStudyMember]

    @extend_schema(
        summary="스터디 탈퇴",
        description="현재 사용자가 스터디에서 탈퇴합니다. 스터디 오너는 탈퇴할 수 없습니다.",
        responses={
            204: None,
            400: ErrorEnvelopeSerializer,
        },
    )
    def delete(self, request, study_id):
        membership = get_object_or_404(
            StudyMember, study_id=study_id, user=request.user
        )

        if membership.role == StudyRole.OWNER:
            return Response(
                {
                    "error_code": "OWNER_CANNOT_LEAVE",
                    "message": "스터디 오너는 탈퇴할 수 없습니다.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        membership.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["studies"])
class StudyListView(APIView):
    """가입한 스터디 목록 조회 API"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="내 스터디 목록 조회",
        description="현재 로그인한 사용자가 가입한 스터디 목록을 조회합니다.",
        responses={200: StudyListSerializer(many=True)},
    )
    def get(self, request):
        # 현재 사용자가 가입한 스터디 목록 조회 (N+1 쿼리 방지를 위해 annotate 사용)
        study_memberships = (
            StudyMember.objects.filter(user=request.user)
            .select_related("study")
            .annotate(member_count=Count("study__members"))
        )

        serializer = StudyListSerializer(study_memberships, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(tags=["daily-assignments"])
class DailyAssignmentView(APIView):
    """일일 문제 배정 API"""

    permission_classes = [IsAuthenticated, IsStudyMember]

    @extend_schema(
        summary="일일 추천 문제 조회",
        description="스터디의 오늘 추천 문제 목록을 조회합니다.",
        responses={200: DailyAssignmentListResponseSerializer},
    )
    def get(self, request, study_id):
        """일일 추천 문제 조회"""
        study = get_object_or_404(Study, id=study_id)
        self.check_object_permissions(request, study)

        service = DailyAssignmentService()

        assignments = service.assign_daily_problems(study)
        can_refresh, remaining = service.can_force_refresh(study)

        # 갱신 시간은 첫 번째 assignment의 created_at 사용
        refreshed_at = assignments[0].created_at if assignments else None

        serializer = DailyAssignmentSerializer(assignments, many=True)
        return Response(
            {
                "assignments": serializer.data,
                "refreshed_at": refreshed_at,
                "can_refresh": can_refresh,
                "refresh_cooldown_seconds": remaining,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="추천 문제 강제 갱신",
        description="스터디의 추천 문제를 강제로 새로 갱신합니다. 5분에 1번만 가능합니다.",
        responses={
            204: None,
            429: ForceRefreshErrorSerializer,
        },
    )
    def post(self, request, study_id):
        """추천 문제 강제 갱신"""
        study = get_object_or_404(Study, id=study_id)
        self.check_object_permissions(request, study)

        service = DailyAssignmentService()

        try:
            service.assign_daily_problems(study, force_refresh=True)
        except RefreshCooldownError as e:
            return Response(
                {
                    "error_code": "REFRESH_COOLDOWN",
                    "message": str(e),
                    "remaining_seconds": e.remaining_seconds,
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)
