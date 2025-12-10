from rest_framework import serializers
from core.models import Study


class StudyDetailSerializer(serializers.ModelSerializer):
    """스터디 상세 조회 Serializer"""

    class Meta:
        model = Study
        fields = [
            "id",
            "name",
            "description",
            "invite_code",
            "daily_problem_count",
            "tier_min",
            "tier_max",
            "min_solved",
            "max_solved",
            "template_content",
            "created_at",
        ]
        read_only_fields = fields
