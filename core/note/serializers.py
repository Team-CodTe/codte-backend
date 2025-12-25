from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from core.models import SolutionNote, Study, DailyAssignment
import datetime


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
    assigned_date = serializers.SerializerMethodField()

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
        ]
        read_only_fields = fields

    @extend_schema_field(serializers.DateField(allow_null=True))
    def get_assigned_date(self, obj):
        """해당 문제의 DailyAssignment에서 assigned_date 조회"""
        assignment = DailyAssignment.objects.filter(
            study=obj.study, problem=obj.problem
        ).first()
        if assignment:
            return assignment.assigned_date
        return None


class StudyTemplateContentSerializer(serializers.ModelSerializer):
    """스터디 템플릿 내용 Response Serializer"""

    class Meta:
        model = Study
        fields = ["template_content"]
        read_only_fields = fields
