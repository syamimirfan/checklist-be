from rest_framework import serializers


class RequestSerializer(serializers.Serializer):
    """Base for request bodies. `validated(data)` returns the clean data, or raises a 400 error."""

    @classmethod
    def validated(cls, data):
        serializer = cls(data=data)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data
