from rest_framework import serializers
from datetime import timedelta

from core.models import SolutionNote, Study


class SolutionNoteCreateSerializer(serializers.Serializer):
    """풀이 노트 생성 Request Serializer"""

    problem_id = serializers.IntegerField(
        required=True, help_text="문제 ID (DB 내부 ID)"
    )
    content = serializers.CharField(required=True, help_text="풀이 본문 (Markdown)")


class SolutionNoteUpdateSerializer(serializers.Serializer):
    """풀이 노트 수정 Request Serializer"""

    content = serializers.CharField(required=True, help_text="풀이 본문 (Markdown)")


class SolutionNoteListQuerySerializer(serializers.Serializer):
    """풀이 노트 목록 조회 Query Serializer"""

    problem_id = serializers.IntegerField(
        required=False, allow_null=True, help_text="문제 ID (DB 내부 ID, 선택)"
    )
    assigned_date = serializers.DateField(
        required=False, allow_null=True, help_text="문제 추천 날짜 (YYYY-MM-DD)"
    )
    created_date = serializers.DateField(
        required=False,
        allow_null=True,
        help_text="작성일 (YYYY-MM-DD)",
    )
    query = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        help_text="통합 검색 (제목, 문제 번호, 작성자)",
    )


class SolutionNoteCreateResponseSerializer(serializers.ModelSerializer):
    """풀이 노트 생성 Response Serializer"""

    class Meta:
        model = SolutionNote
        fields = ["id"]
        read_only_fields = fields


class SolutionNoteResponseSerializer(serializers.ModelSerializer):
    """풀이 노트 Response Serializer"""

    username = serializers.CharField(source="user.username", read_only=True)
    problem_id = serializers.IntegerField(source="problem.id", read_only=True)
    problem_title = serializers.CharField(source="problem.title", read_only=True)
    problem_boj_number = serializers.IntegerField(
        source="problem.boj_number", read_only=True
    )
    problem_boj_tier = serializers.IntegerField(source="problem.tier", read_only=True)
    problem_link = serializers.URLField(source="problem.link", read_only=True)
    is_updated = serializers.SerializerMethodField(help_text="수정 여부")

    class Meta:
        model = SolutionNote
        fields = [
            "id",
            "username",
            "problem_id",
            "problem_title",
            "problem_boj_number",
            "problem_boj_tier",
            "problem_link",
            "assigned_date",
            "content",
            "created_at",
            "updated_at",
            "is_updated",
        ]
        read_only_fields = fields

    def get_is_updated(self, obj: SolutionNote) -> bool:
        if obj.created_at is None or obj.updated_at is None:
            return False
        return (obj.updated_at - obj.created_at) > timedelta(seconds=1)


class StudyTemplateContentSerializer(serializers.ModelSerializer):
    """스터디 템플릿 내용 Response Serializer"""

    class Meta:
        model = Study
        fields = ["template_content"]
        read_only_fields = fields


class CodeReviewResponseSerializer(serializers.Serializer):
    """코드 리뷰 Response Serializer"""

    id = serializers.IntegerField(read_only=True, help_text="코드 리뷰 ID")
    review_content = serializers.CharField(
        read_only=True, help_text="리뷰 내용 (Markdown)"
    )
    created_at = serializers.DateTimeField(read_only=True, help_text="생성일시")
    updated_at = serializers.DateTimeField(read_only=True, help_text="수정일시")
