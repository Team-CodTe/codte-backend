from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from core.models import Study
from core.common.serializers import ErrorEnvelopeSerializer
from core.study.permissions import IsStudyMember
from core.utils.solvedac import ProblemNotFoundError

from .serializers import (
    CustomAssignmentAddSerializer,
    DailyAssignmentListResponseSerializer,
    DailyAssignmentSerializer,
    ForceRefreshErrorSerializer,
)
from .services import (
    AlreadyAssignedError,
    DailyAssignmentService,
    RefreshCooldownError,
)


@extend_schema(tags=["assignments"])
class DailyAssignmentView(APIView):
    """오늘의 추천 문제 API"""

    permission_classes = [IsAuthenticated, IsStudyMember]

    @extend_schema(
        summary="오늘의 추천 문제 조회",
        description="스터디의 오늘 추천 문제 목록을 조회합니다.",
        responses={200: DailyAssignmentListResponseSerializer},
    )
    def get(self, request, study_id):
        """오늘의 추천 문제 조회"""
        study = get_object_or_404(Study, id=study_id)
        self.check_object_permissions(request, study)

        service = DailyAssignmentService()

        # 자동 배정 문제 생성 (이미 있으면 스킵)
        service.assign_daily_problems(study)

        # 커스텀 문제 포함 전체 조회
        assignments = service.get_daily_assignments(study)
        can_refresh, next_refresh_available_at = service.can_force_refresh(study)

        # 자동 배정된 문제 중 가장 최근 생성 시간을 갱신 시간으로 사용
        auto_assignments = [a for a in assignments if not a.is_custom]
        refreshed_at = (
            max(a.created_at for a in auto_assignments) if auto_assignments else None
        )

        response_data = {
            "assignments": assignments,
            "refreshed_at": refreshed_at,
            "can_refresh": can_refresh,
            "next_refresh_available_at": next_refresh_available_at,
        }
        serializer = DailyAssignmentListResponseSerializer(instance=response_data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="오늘의 추천 문제 강제 갱신",
        description="스터디의 오늘 추천 문제를 강제로 새로 갱신합니다. 30분에 1번만 가능합니다.",
        responses={
            204: None,
            429: ForceRefreshErrorSerializer,
        },
    )
    def post(self, request, study_id):
        """오늘의 추천 문제 강제 갱신"""
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
                    "next_available_at": e.next_available_at,
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["assignments"])
class CustomAssignmentAddView(APIView):
    """커스텀 문제 추가 API"""

    permission_classes = [IsAuthenticated, IsStudyMember]

    @extend_schema(
        summary="커스텀 문제 추가",
        description="백준 문제 번호를 입력받아 오늘의 추천 문제에 추가합니다.",
        request=CustomAssignmentAddSerializer,
        responses={
            201: None,
            400: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
        },
    )
    def post(self, request, study_id):
        study = get_object_or_404(Study, id=study_id)
        self.check_object_permissions(request, study)

        serializer = CustomAssignmentAddSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        boj_number = serializer.validated_data["boj_number"]
        service = DailyAssignmentService()

        try:
            service.add_custom_assignment(study, boj_number)
        except AlreadyAssignedError as e:
            return Response(
                {
                    "error_code": "ALREADY_ASSIGNED",
                    "message": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ProblemNotFoundError as e:
            return Response(
                {
                    "error_code": "PROBLEM_NOT_FOUND",
                    "message": str(e),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(status=status.HTTP_201_CREATED)
