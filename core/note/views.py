from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from .serializers import SolutionNoteCreateSerializer, SolutionNoteResponseSerializer
from core.common.serializers import ErrorEnvelopeSerializer
from .services import SolutionNoteService


@extend_schema(tags=["notes"])
class SolutionNoteCreateView(APIView):
    """풀이 노트 작성 API"""

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
        problem_id = serializer.validated_data["problem_id"]
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
