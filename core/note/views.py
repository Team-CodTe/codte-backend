from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .serializers import (
    SolutionNoteCreateSerializer,
    SolutionNoteUpdateSerializer,
    SolutionNoteListQuerySerializer,
    SolutionNoteResponseSerializer,
    StudyTemplateContentSerializer,
)
from core.common.serializers import ErrorEnvelopeSerializer
from core.common.pagination import StandardResultsSetPagination
from .services import SolutionNoteService


@extend_schema(tags=["notes"])
class SolutionNoteView(APIView):
    """풀이 노트 목록 조회 및 생성 API"""

    permission_classes = [IsAuthenticated]
    service_class = SolutionNoteService
    pagination_class = StandardResultsSetPagination

    @extend_schema(
        summary="풀이 노트 목록 조회",
        description="특정 스터디의 풀이 노트 목록을 조회합니다. 스터디 멤버만 조회 가능합니다.",
        parameters=[
            OpenApiParameter(
                name="problem_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="문제 ID (DB 내부 ID, 선택)",
                required=False,
            ),
            OpenApiParameter(
                name="page",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="페이지 번호 (기본값: 1)",
                required=False,
            ),
            OpenApiParameter(
                name="page_size",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="페이지 크기 (기본값: 10, 최대: 100)",
                required=False,
                default=10,
            ),
        ],
        responses={
            200: SolutionNoteResponseSerializer(many=True),
            400: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
        },
    )
    def get(self, request, study_id):
        # Query 파라미터 검증
        serializer = SolutionNoteListQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        problem_id = serializer.validated_data.get("problem_id")

        try:
            service = self.service_class()
            solution_notes = service.get_solution_notes(
                user=request.user,
                study_id=study_id,
                problem_id=problem_id,
            )
        except ValueError as e:
            return Response(
                {
                    "error_code": "PERMISSION_DENIED",
                    "message": str(e),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # DRF 페이지네이션 적용
        paginator = self.pagination_class()
        paginated_notes = paginator.paginate_queryset(
            solution_notes, request, view=self
        )
        response_serializer = SolutionNoteResponseSerializer(paginated_notes, many=True)
        return paginator.get_paginated_response(response_serializer.data)

    @extend_schema(
        summary="풀이 노트 작성",
        description="스터디의 문제에 대한 풀이 노트를 작성합니다. 스터디 멤버만 작성 가능하며, 같은 문제에 대한 노트는 하나만 작성할 수 있습니다.",
        request=SolutionNoteCreateSerializer,
        responses={
            201: SolutionNoteResponseSerializer,
            400: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
        },
    )
    def post(self, request, study_id):
        serializer = SolutionNoteCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        problem_id = serializer.validated_data.get("problem_id")
        content = serializer.validated_data["content"]

        try:
            service = self.service_class()
            solution_note = service.create_solution_note(
                user=request.user,
                study_id=study_id,
                problem_id=problem_id,
                content=content,
            )
        except ValueError as e:
            return Response(
                {
                    "error_code": "INVALID_REQUEST",
                    "message": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = SolutionNoteResponseSerializer(solution_note)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["notes"])
class SolutionNoteDetailView(APIView):
    """풀이 노트 상세 조회, 수정, 삭제 API"""

    permission_classes = [IsAuthenticated]
    service_class = SolutionNoteService

    @extend_schema(
        summary="풀이 노트 상세 조회",
        description="특정 풀이 노트의 전체 내용을 조회합니다. 스터디 멤버만 조회 가능합니다.",
        responses={
            200: SolutionNoteResponseSerializer,
            403: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
        },
    )
    def get(self, request, note_id):
        try:
            service = self.service_class()
            solution_note = service.get_solution_note(
                user=request.user,
                note_id=note_id,
            )
        except ValueError as e:
            return Response(
                {
                    "error_code": "PERMISSION_DENIED",
                    "message": str(e),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        response_serializer = SolutionNoteResponseSerializer(solution_note)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="풀이 노트 수정",
        description="풀이 노트의 내용을 수정합니다. 노트 작성자만 수정 가능합니다.",
        request=SolutionNoteUpdateSerializer,
        responses={
            200: SolutionNoteResponseSerializer,
            400: ErrorEnvelopeSerializer,
            403: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
        },
    )
    def patch(self, request, note_id):
        serializer = SolutionNoteUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        content = serializer.validated_data["content"]

        try:
            service = self.service_class()
            solution_note = service.update_solution_note(
                user=request.user,
                note_id=note_id,
                content=content,
            )
        except ValueError as e:
            return Response(
                {
                    "error_code": "PERMISSION_DENIED",
                    "message": str(e),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        response_serializer = SolutionNoteResponseSerializer(solution_note)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="풀이 노트 삭제",
        description="풀이 노트를 삭제합니다. 노트 작성자만 삭제 가능합니다.",
        responses={
            204: None,
            403: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
        },
    )
    def delete(self, request, note_id):
        try:
            service = self.service_class()
            service.delete_solution_note(
                user=request.user,
                note_id=note_id,
            )
        except ValueError as e:
            return Response(
                {
                    "error_code": "PERMISSION_DENIED",
                    "message": str(e),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["notes"])
class SolutionNoteTemplateView(APIView):
    """스터디 템플릿 내용 조회 API"""

    permission_classes = [IsAuthenticated]
    service_class = SolutionNoteService

    @extend_schema(
        summary="스터디 템플릿 내용 조회",
        description="해당 스터디의 템플릿 내용을 조회합니다. 스터디 멤버만 조회 가능합니다.",
        responses={
            200: StudyTemplateContentSerializer,
            403: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
        },
    )
    def get(self, request, study_id):
        try:
            service = self.service_class()
            study = service.get_study_template_content(
                user=request.user,
                study_id=study_id,
            )
        except ValueError as e:
            return Response(
                {
                    "error_code": "PERMISSION_DENIED",
                    "message": str(e),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        response_serializer = StudyTemplateContentSerializer(study)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
