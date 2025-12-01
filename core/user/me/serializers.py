from rest_framework import serializers
from core.models import User


class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "provider",
            "boj_username",
            "profile_img_url",
            "created_at",
        ]
        read_only_fields = fields
