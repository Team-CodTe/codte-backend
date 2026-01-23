from rest_framework import serializers


class ErrorEnvelopeSerializer(serializers.Serializer):
    error_code = serializers.CharField()
    message = serializers.CharField()
