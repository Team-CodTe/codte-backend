from rest_framework import serializers

from core.models import DailyAssignment


class DailyAssignmentSerializer(serializers.ModelSerializer):
    """오늘의 추천 문제 Serializer"""

    problem_id = serializers.IntegerField(source="problem.id", read_only=True)
    boj_number = serializers.IntegerField(source="problem.boj_number", read_only=True)
    title = serializers.CharField(source="problem.title", read_only=True)
    tier = serializers.IntegerField(source="problem.tier", read_only=True)
    link = serializers.URLField(source="problem.link", read_only=True)

    class Meta:
        model = DailyAssignment
        fields = [
            "id",
            "problem_id",
            "boj_number",
            "title",
            "tier",
            "link",
            "assigned_date",
            "is_custom",
        ]


class DailyAssignmentListResponseSerializer(serializers.Serializer):
    """오늘의 추천 문제 목록 응답 Serializer"""

    assignments = DailyAssignmentSerializer(many=True)
    refreshed_at = serializers.DateTimeField(
        help_text="문제 리스트 갱신 시간", allow_null=True
    )
    can_refresh = serializers.BooleanField(help_text="강제 갱신 가능 여부")
    next_refresh_available_at = serializers.DateTimeField(
        help_text="다음 강제 갱신 가능 시간", allow_null=True
    )


class ForceRefreshErrorSerializer(serializers.Serializer):
    """강제 갱신 에러 Serializer"""

    error_code = serializers.CharField()
    message = serializers.CharField()
    next_available_at = serializers.DateTimeField(required=False)


class CustomAssignmentAddSerializer(serializers.Serializer):
    """커스텀 문제 추가 Serializer"""

    boj_number = serializers.IntegerField(
        required=True,
        help_text="백준 문제 번호",
        min_value=1,
    )
