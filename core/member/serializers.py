from rest_framework import serializers

from core.models import StudyMember


class StudyMemberListSerializer(serializers.ModelSerializer):
    """스터디 멤버 목록 Serializer"""

    id = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    boj_username = serializers.CharField(
        source="user.boj_username", read_only=True, allow_null=True
    )
    role = serializers.CharField(read_only=True)
    joined_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = StudyMember
        fields = [
            "id",
            "username",
            "email",
            "boj_username",
            "role",
            "joined_at",
        ]
