from rest_framework import serializers

from core.common.serializers import ErrorEnvelopeSerializer
from core.models import Study, StudyMember


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
            "daily_problem_count": {"required": True},
            "tier_min": {"required": True},
            "tier_max": {"required": True},
            "min_solved": {"required": False, "allow_null": True},
            "max_solved": {"required": False, "allow_null": True},
        }


class StudyDetailSerializer(serializers.ModelSerializer):
    """스터디 상세 조회 Serializer"""

    my_role = serializers.CharField(source="current_user_role", read_only=True)

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
            "my_role",
        ]
        read_only_fields = fields


class StudyUpdateSerializer(serializers.ModelSerializer):
    """스터디 수정 Serializer"""

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
        read_only_fields = ["id", "invite_code", "created_at"]
        extra_kwargs = {
            "name": {"required": False},
            "description": {"required": False, "allow_blank": True},
            "daily_problem_count": {"required": False},
            "tier_min": {"required": False},
            "tier_max": {"required": False},
            "min_solved": {"required": False, "allow_null": True},
            "max_solved": {"required": False, "allow_null": True},
            "template_content": {"required": False},
        }


class StudyJoinSerializer(serializers.Serializer):
    """스터디 가입 Serializer"""

    invite_code = serializers.CharField(
        max_length=8, required=True, help_text="초대 코드"
    )


class StudyListSerializer(serializers.ModelSerializer):
    """가입한 스터디 목록 Serializer"""

    study_id = serializers.IntegerField(source="study.id", read_only=True)
    study_name = serializers.CharField(source="study.name", read_only=True)
    member_count = serializers.IntegerField(read_only=True)
    role = serializers.CharField(read_only=True)
    joined_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = StudyMember
        fields = [
            "study_id",
            "study_name",
            "member_count",
            "role",
            "joined_at",
        ]


class StudyCreateErrorSerializer(serializers.Serializer):
    name = serializers.ListField(child=serializers.CharField(), required=False)
    description = serializers.ListField(child=serializers.CharField(), required=False)
    daily_problem_count = serializers.ListField(
        child=serializers.CharField(), required=False
    )
    tier_min = serializers.ListField(child=serializers.CharField(), required=False)
    tier_max = serializers.ListField(child=serializers.CharField(), required=False)


class StudyJoinResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
