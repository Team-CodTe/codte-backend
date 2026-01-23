from rest_framework import serializers

from core.common.serializers import ErrorEnvelopeSerializer


class SocialLoginRequestSerializer(serializers.Serializer):
    provider = serializers.ChoiceField(
        choices=["google", "github"],
        help_text="OAuth 제공자 (google, github)",
    )
    access_token = serializers.CharField(help_text="OAuth access token")


class SocialLoginUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    provider = serializers.CharField()
    email = serializers.EmailField()
    username = serializers.CharField()
    boj_username = serializers.CharField(allow_null=True)
    profile_img_url = serializers.URLField(allow_null=True)


class SocialLoginResponseSerializer(serializers.Serializer):
    user = SocialLoginUserSerializer()
    is_registered = serializers.BooleanField(help_text="회원가입 완료 여부")
