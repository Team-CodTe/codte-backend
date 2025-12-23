from rest_framework import serializers
from core.models import SolutionNote


class SolutionNoteCreateSerializer(serializers.Serializer):
    """풀이 노트 생성 Request Serializer"""

    study_id = serializers.IntegerField(required=True, help_text="스터디 ID")
    problem_id = serializers.IntegerField(required=True, help_text="문제 ID (DB 내부 ID)")
    content = serializers.CharField(required=True, help_text="풀이 본문 (Markdown)")


class SolutionNoteResponseSerializer(serializers.ModelSerializer):
    """풀이 노트 생성 Response Serializer"""

    user_nickname = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = SolutionNote
        fields = [
            "id",
            "user_nickname",
            "content",
            "created_at",
        ]
        read_only_fields = fields
