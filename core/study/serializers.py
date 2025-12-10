from rest_framework import serializers
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
            "daily_problem_count": {"required": False},
            "tier_min": {"required": True},
            "tier_max": {"required": True},
            "min_solved": {"required": False, "allow_null": True},
            "max_solved": {"required": False, "allow_null": True},
        }


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

    study_name = serializers.CharField(source="study.name", read_only=True)
    member_count = serializers.SerializerMethodField()
    role = serializers.CharField(read_only=True)
    joined_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = StudyMember
        fields = [
            "study_name",
            "member_count",
            "role",
            "joined_at",
        ]

    def get_member_count(self, obj):
        """스터디의 멤버 수 반환"""
        return obj.study.members.count()
