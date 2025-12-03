from rest_framework import serializers
from core.user.validators import (
    validate_boj_username_for_user,
    validate_username_for_user,
)


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
