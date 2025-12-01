from rest_framework import serializers
from core.models import User


class UserSignUpSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True, min_length=2, max_length=20)
    boj_username = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ["username", "boj_username"]

    def validate_username(self, value):
        user = self.context["request"].user

        if User.objects.filter(username=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("이미 존재하는 닉네임입니다.")

        return value

    def validate_boj_username(self, value):
        user = self.context["request"].user

        if User.objects.filter(boj_username=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("이미 존재하는 백준 계정입니다.")

        return value

    def update(self, instance, validated_data):
        instance.username = validated_data.get("username", instance.username)
        instance.boj_username = validated_data.get(
            "boj_username", instance.boj_username
        )

        instance.save()

        return instance
