from rest_framework import serializers
from core.models import SolutionNote


class SolutionNoteCreateSerializer(serializers.Serializer):
    """풀이 노트 생성 Request Serializer"""

    study_id = serializers.IntegerField(required=True, help_text="스터디 ID")
    problem_id = serializers.IntegerField(required=True, help_text="문제 ID (DB 내부 ID)")
    content = serializers.CharField(required=True, help_text="풀이 본문 (Markdown)")


class SolutionNoteUpdateSerializer(serializers.Serializer):
    """풀이 노트 수정 Request Serializer"""

    note_id = serializers.IntegerField(required=True, help_text="풀이 노트 ID")
    content = serializers.CharField(required=True, help_text="풀이 본문 (Markdown)")


class SolutionNoteDeleteSerializer(serializers.Serializer):
    """풀이 노트 삭제 Request Serializer"""

    note_id = serializers.IntegerField(required=True, help_text="풀이 노트 ID")


class SolutionNoteResponseSerializer(serializers.ModelSerializer):
    """풀이 노트 Response Serializer"""

    user_nickname = serializers.CharField(source="user.username", read_only=True)
    study_id = serializers.IntegerField(source="study.id", read_only=True)
    study_name = serializers.CharField(source="study.name", read_only=True)
    problem_id = serializers.IntegerField(source="problem.id", read_only=True)
    problem_title = serializers.CharField(source="problem.title", read_only=True)
    problem_boj_number = serializers.IntegerField(source="problem.boj_number", read_only=True)

    class Meta:
        model = SolutionNote
        fields = [
            "id",
            "user_nickname",
            "study_id",
            "study_name",
            "problem_id",
            "problem_title",
            "problem_boj_number",
            "content",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
