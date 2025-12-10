from rest_framework import serializers


class StudyJoinSerializer(serializers.Serializer):
    """스터디 가입 Serializer"""

    invite_code = serializers.CharField(
        max_length=8, required=True, help_text="초대 코드"
    )
