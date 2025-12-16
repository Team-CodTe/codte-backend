from rest_framework import serializers
from core.models import User
from core.user.validators import (
    validate_boj_username_for_user,
    validate_username_for_user,
)


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


class UseProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True, min_length=2, max_length=20)
    boj_username = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ["username", "boj_username"]

    def validate_username(self, value):
        user = self.context["request"].user
        return validate_username_for_user(user, value)

    def validate_boj_username(self, value):
        user = self.context["request"].user
        return validate_boj_username_for_user(user, value)


class UsernameValidationSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, min_length=2, max_length=20)

    def validate_username(self, value):
        user = self.context["request"].user
        return validate_username_for_user(user, value)


class BojUsernameValidationSerializer(serializers.Serializer):
    boj_username = serializers.CharField(required=True)

    def validate_boj_username(self, value):
        user = self.context["request"].user
        return validate_boj_username_for_user(user, value)
