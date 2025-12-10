from rest_framework import serializers
from core.models import Study


class StudyCreateSerializer(serializers.ModelSerializer):
    """스터디 생성 Serializer"""

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
            "created_at",
        ]
        read_only_fields = ["id", "invite_code", "created_at"]
        extra_kwargs = {
            "name": {"required": True},
            "description": {"required": False, "allow_blank": True},
            "daily_problem_count": {"required": False},
            "tier_min": {"required": True},
            "tier_max": {"required": True},
            "min_solved": {"required": False, "allow_null": True},
            "max_solved": {"required": False, "allow_null": True},
        }
