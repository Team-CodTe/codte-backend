import requests
from rest_framework import serializers
from core.models import User


def _validate_username_for_user(user, value: str) -> str:
    if User.objects.filter(username=value).exclude(id=user.id).exists():
        raise serializers.ValidationError("이미 존재하는 닉네임입니다.")

    return value


def _validate_boj_username_for_user(user, value: str) -> str:
    if User.objects.filter(boj_username=value).exclude(id=user.id).exists():
        raise serializers.ValidationError("이미 존재하는 백준 계정입니다.")

    try:
        response = requests.get(
            f"https://solved.ac/api/v3/user/show?handle={value}",
            timeout=5,
        )
        if response.status_code == 404:
            raise serializers.ValidationError("존재하지 않는 백준 계정입니다.")
        if response.status_code != 200:
            raise serializers.ValidationError(
                "백준 계정 확인 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            )
    except requests.RequestException:
        raise serializers.ValidationError(
            "백준 계정 확인 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        )

    return value


class UserSignUpSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True, min_length=2, max_length=20)
    boj_username = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ["username", "boj_username"]

    def validate_username(self, value):
        user = self.context["request"].user
        return _validate_username_for_user(user, value)

    def validate_boj_username(self, value):
        user = self.context["request"].user
        return _validate_boj_username_for_user(user, value)


class UsernameValidationSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, min_length=2, max_length=20)

    def validate_username(self, value):
        user = self.context["request"].user
        return _validate_username_for_user(user, value)


class BojUsernameValidationSerializer(serializers.Serializer):
    boj_username = serializers.CharField(required=True)

    def validate_boj_username(self, value):
        user = self.context["request"].user
        return _validate_boj_username_for_user(user, value)
