from rest_framework import serializers
from core.models import SolutionNote, Study


class SolutionNoteCreateSerializer(serializers.Serializer):
    """풀이 노트 생성 Request Serializer"""

    study_id = serializers.IntegerField(required=True, help_text="스터디 ID")
    problem_id = serializers.IntegerField(required=True, help_text="문제 ID (DB 내부 ID)")
    content = serializers.CharField(required=True, help_text="풀이 본문 (Markdown)")


class SolutionNoteUpdateSerializer(serializers.Serializer):
    """풀이 노트 수정 Request Serializer"""

    content = serializers.CharField(required=True, help_text="풀이 본문 (Markdown)")


class SolutionNoteListQuerySerializer(serializers.Serializer):
    """풀이 노트 목록 조회 Query Serializer"""

    study_id = serializers.IntegerField(required=True, help_text="스터디 ID")
    problem_id = serializers.IntegerField(required=False, allow_null=True, help_text="문제 ID (DB 내부 ID, 선택)")


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


class StudyTemplateContentSerializer(serializers.ModelSerializer):
    """스터디 템플릿 내용 Response Serializer"""

    class Meta:
        model = Study
        fields = ["template_content"]
        read_only_fields = fields
