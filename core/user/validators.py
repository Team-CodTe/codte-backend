import requests
from rest_framework import serializers

from core.models import User

SOLVED_AC_USER_API_URL = "https://solved.ac/api/v3/user/show?handle={handle}"


def validate_username_for_user(user, value: str) -> str:
    if User.objects.filter(username=value).exclude(id=user.id).exists():
        raise serializers.ValidationError("이미 사용 중인 닉네임입니다.")

    return value


def validate_boj_username_for_user(user, value: str) -> str:
    if User.objects.filter(boj_username=value).exclude(id=user.id).exists():
        raise serializers.ValidationError("이미 사용 중인 백준 계정입니다.")

    try:
        response = requests.get(
            SOLVED_AC_USER_API_URL.format(handle=value),
            timeout=5,
        )
        if response.status_code == 404:
            raise serializers.ValidationError("존재하지 않는 백준 계정입니다.")
        if response.status_code != 200:
            raise serializers.ValidationError("백준 계정 확인 중 오류가 발생했습니다.")
    except requests.RequestException:
        raise serializers.ValidationError("백준 계정 확인 중 오류가 발생했습니다.")

    return value
