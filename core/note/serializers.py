from rest_framework import serializers

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
        """created_at과 updated_at을 비교하여 수정 여부 반환"""
        return obj.created_at != obj.updated_at


class StudyTemplateContentSerializer(serializers.ModelSerializer):
    """스터디 템플릿 내용 Response Serializer"""

    class Meta:
        model = Study
        fields = ["template_content"]
        read_only_fields = fields
