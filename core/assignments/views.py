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

        # 자동 배정 문제 생성 (이미 있으면 스킵)
        service.assign_daily_problems(study)

        # 커스텀 문제 포함 전체 조회
        assignments = service.get_daily_assignments(study)
        can_refresh, next_refresh_available_at = service.can_force_refresh(study)

        # 갱신 시간은 첫 번째 assignment의 created_at 사용
        refreshed_at = assignments[0].created_at if assignments else None

        serializer = DailyAssignmentSerializer(assignments, many=True)
        return Response(
            {
                "assignments": serializer.data,
                "refreshed_at": refreshed_at,
                "next_refresh_available_at": next_refresh_available_at,
                "can_refresh": can_refresh,
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
                    "next_available_at": e.next_available_at,
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["daily-assignments"])
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
            service.add_custom_problem(study, boj_number)
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
