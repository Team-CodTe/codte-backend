from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from core.models import Study
from core.common.serializers import ErrorEnvelopeSerializer
from core.study.permissions import IsStudyMember

from .serializers import (
    AssignmentStatusQuerySerializer,
    AssignmentStatusResponseSerializer,
    GroupAssignmentStatusResponseSerializer,
    ProblemMembersStatusResponseSerializer,
    StatisticsQuerySerializer,
    MyStatisticsResponseSerializer,
    GroupStatisticsResponseSerializer,
    MemberStatisticsResponseSerializer,
    UpdateCooldownErrorSerializer,
)
from .services import ProblemSolvingStatusService, UpdateCooldownError


@extend_schema(tags=["problem_solving_status"])
class ProblemStatusUpdateView(APIView):
    """문제 풀이 상태 업데이트 API"""

    permission_classes = [IsAuthenticated, IsStudyMember]

    @extend_schema(
        summary="문제 풀이 상태 업데이트",
        description="오늘의 추천 문제 풀이 상태를 백준 API로 자동 확인하여 업데이트합니다. 5분마다 1번만 가능합니다.",
        request=None,
        responses={
            200: None,
            429: UpdateCooldownErrorSerializer,
            400: ErrorEnvelopeSerializer,
        },
    )
    def post(self, request, study_id):
        """문제 풀이 상태 업데이트"""
        study = get_object_or_404(Study, id=study_id)
        self.check_object_permissions(request, study)

        service = ProblemSolvingStatusService()

        try:
            service.update_solving_status(
                user=request.user,
                study_id=study_id,
            )
        except UpdateCooldownError as e:
            return Response(
                {
                    "error_code": "UPDATE_COOLDOWN",
                    "message": str(e),
                    "next_available_at": e.next_available_at,
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        except ValueError as e:
            return Response(
                {
                    "error_code": "INVALID_REQUEST",
                    "message": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(status=status.HTTP_200_OK)


@extend_schema(tags=["problem_solving_status"])
class ProblemStatusView(APIView):
    """문제 풀이 상태 조회 API"""

    permission_classes = [IsAuthenticated, IsStudyMember]

    @extend_schema(
        summary="문제 풀이 상태 조회",
        description="오늘의 추천 문제 풀이 상태를 조회합니다.",
        parameters=[
            OpenApiParameter(
                name="date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="날짜 (YYYY-MM-DD, 기본값: 오늘)",
                required=False,
            ),
            OpenApiParameter(
                name="view",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="조회 방식 (me: 현재 사용자, group: 모든 멤버, 기본값: me)",
                required=False,
                enum=["me", "group"],
            ),
        ],
        responses={
            200: AssignmentStatusResponseSerializer,
            400: ErrorEnvelopeSerializer,
        },
    )
    def get(self, request, study_id):
        """문제 풀이 상태 조회"""
        study = get_object_or_404(Study, id=study_id)
        self.check_object_permissions(request, study)

        # Query 파라미터 검증
        serializer = AssignmentStatusQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        target_date = serializer.validated_data.get("date")
        view = serializer.validated_data.get("view", "me")

        service = ProblemSolvingStatusService()
        result = service.get_solving_statuses(
            user=request.user,
            study_id=study_id,
            target_date=target_date,
            view=view,
        )

        # view에 따라 다른 serializer 사용
        if view == "me":
            response_serializer = AssignmentStatusResponseSerializer(instance=result)
        else:  # view == "group"
            response_serializer = GroupAssignmentStatusResponseSerializer(
                instance=result
            )

        return Response(response_serializer.data, status=status.HTTP_200_OK)


@extend_schema(tags=["problem_solving_status"])
class ProblemMembersStatusView(APIView):
    """특정 문제의 모든 멤버 풀이 상태 조회 API"""

    permission_classes = [IsAuthenticated, IsStudyMember]

    @extend_schema(
        summary="특정 문제의 모든 멤버 풀이 상태 조회",
        description="특정 문제에 대한 모든 멤버의 풀이 상태를 조회합니다.",
        responses={
            200: ProblemMembersStatusResponseSerializer,
            404: ErrorEnvelopeSerializer,
        },
    )
    def get(self, request, study_id, problem_id):
        """특정 문제의 모든 멤버 풀이 상태 조회"""
        study = get_object_or_404(Study, id=study_id)
        self.check_object_permissions(request, study)

        service = ProblemSolvingStatusService()
        result = service.get_problem_members_status(
            study_id=study_id, problem_id=problem_id
        )

        response_serializer = ProblemMembersStatusResponseSerializer(instance=result)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


@extend_schema(tags=["problem_solving_status"])
class StatisticsView(APIView):
    """문제 풀이 통계 조회 API"""

    permission_classes = [IsAuthenticated, IsStudyMember]

    @extend_schema(
        summary="문제 풀이 통계 조회",
        description="문제 풀이 통계를 조회합니다.",
        parameters=[
            OpenApiParameter(
                name="view",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="조회 방식 (me: 현재 사용자, group: 모든 멤버, member: 특정 멤버, 기본값: me)",
                required=False,
                enum=["me", "group", "member"],
            ),
            OpenApiParameter(
                name="member_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="멤버 ID (view=member일 때 필수)",
                required=False,
            ),
            OpenApiParameter(
                name="start_date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="시작 날짜 (YYYY-MM-DD)",
                required=False,
            ),
            OpenApiParameter(
                name="end_date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="종료 날짜 (YYYY-MM-DD)",
                required=False,
            ),
        ],
        responses={
            200: MyStatisticsResponseSerializer,
            400: ErrorEnvelopeSerializer,
        },
    )
    def get(self, request, study_id):
        """문제 풀이 통계 조회"""
        study = get_object_or_404(Study, id=study_id)
        self.check_object_permissions(request, study)

        # Query 파라미터 검증
        serializer = StatisticsQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        view = serializer.validated_data.get("view", "me")
        member_id = serializer.validated_data.get("member_id")
        start_date = serializer.validated_data.get("start_date")
        end_date = serializer.validated_data.get("end_date")

        service = ProblemSolvingStatusService()
        result = service.get_statistics(
            user=request.user,
            study_id=study_id,
            view=view,
            member_id=member_id,
            start_date=start_date,
            end_date=end_date,
        )

        # view에 따라 다른 serializer 사용
        if view == "me":
            response_serializer = MyStatisticsResponseSerializer(instance=result)
        elif view == "group":
            response_serializer = GroupStatisticsResponseSerializer(instance=result)
        else:  # view == "member"
            response_serializer = MemberStatisticsResponseSerializer(instance=result)

        return Response(response_serializer.data, status=status.HTTP_200_OK)
