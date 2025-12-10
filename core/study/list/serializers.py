from rest_framework import serializers
from core.models import StudyMember


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
