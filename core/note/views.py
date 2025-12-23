from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from .serializers import (
    SolutionNoteCreateSerializer,
    SolutionNoteUpdateSerializer,
    SolutionNoteDeleteSerializer,
    SolutionNoteListQuerySerializer,
    SolutionNoteResponseSerializer,
)
from core.common.serializers import ErrorEnvelopeSerializer
from .services import SolutionNoteService


@extend_schema(tags=["notes"])
class SolutionNoteView(APIView):
    """풀이 노트 작성, 수정, 삭제 API"""

    permission_classes = [IsAuthenticated]
    service_class = SolutionNoteService

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
    def post(self, request):
        serializer = SolutionNoteCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        study_id = serializer.validated_data["study_id"]
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
        return Response(
            response_serializer.data, status=status.HTTP_201_CREATED
        )

    @extend_schema(
        summary="풀이 노트 수정",
        description="풀이 노트의 내용을 수정합니다. 노트 작성자만 수정 가능합니다.",
        request=SolutionNoteUpdateSerializer,
        responses={
            200: SolutionNoteResponseSerializer,
            400: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
        },
    )
    def patch(self, request):
        serializer = SolutionNoteUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        note_id = serializer.validated_data["note_id"]
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
        request=SolutionNoteDeleteSerializer,
        responses={
            204: None,
            400: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
        },
    )
    def delete(self, request):
        serializer = SolutionNoteDeleteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        note_id = serializer.validated_data["note_id"]

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
class SolutionNoteListView(APIView):
    """풀이 노트 목록 조회 API"""

    permission_classes = [IsAuthenticated]
    service_class = SolutionNoteService

    @extend_schema(
        summary="풀이 노트 목록 조회",
        description="특정 문제에 대해 스터디원들이 작성한 풀이 노트 목록을 조회합니다. 스터디 멤버만 조회 가능합니다.",
        parameters=[
            {
                "name": "study_id",
                "in": "query",
                "required": True,
                "schema": {"type": "integer"},
                "description": "스터디 ID",
            },
            {
                "name": "problem_id",
                "in": "query",
                "required": False,
                "schema": {"type": "integer"},
                "description": "문제 ID (DB 내부 ID, 선택)",
            },
            {
                "name": "page",
                "in": "query",
                "required": False,
                "schema": {"type": "integer", "default": 1, "minimum": 1},
                "description": "페이지 번호 (기본값: 1)",
            },
            {
                "name": "page_size",
                "in": "query",
                "required": False,
                "schema": {"type": "integer", "default": 10, "minimum": 1, "maximum": 100},
                "description": "페이지 크기 (기본값: 10, 최대: 100)",
            },
        ],
        responses={
             200: {
                "type": "object",
                "properties": {
                    "count": {"type": "integer"},
                    "next": {"type": "string", "nullable": True},
                    "previous": {"type": "string", "nullable": True},
                    "results": {
                        "type": "array",
                        "items": SolutionNoteResponseSerializer,
                    },
                },
            },
            400: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
        },
    )
    def get(self, request):
        # Query 파라미터 검증
        serializer = SolutionNoteListQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        study_id = serializer.validated_data["study_id"]
        problem_id = serializer.validated_data.get("problem_id")
        page = serializer.validated_data.get("page", 1)
        page_size = serializer.validated_data.get("page_size", 10)

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

        # 전체 개수 계산
        total_count = solution_notes.count()

        # Pagination 적용
        start = (page - 1) * page_size
        end = start + page_size
        paginated_notes = solution_notes[start:end]

        response_serializer = SolutionNoteResponseSerializer(paginated_notes, many=True)

        # 다음 페이지 존재 여부 확인
        has_next = end < total_count
        has_previous = page > 1

        # URL 파라미터 구성
        def build_url(page_num):
            params = [f"study_id={study_id}", f"page={page_num}", f"page_size={page_size}"]
            if problem_id is not None:
                params.insert(1, f"problem_id={problem_id}")
            return "?" + "&".join(params)

        return Response(
            {
                "count": total_count,
                "next": build_url(page + 1) if has_next else None,
                "previous": build_url(page - 1) if has_previous else None,
                "results": response_serializer.data,
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=["notes"])
class SolutionNoteDetailView(APIView):
    """풀이 노트 상세 조회 API"""

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
