"""Request bodies are checked for shape here; the rules about *who* may do what live in the services."""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.core.serializers import RequestSerializer

MAX_PASSWORD_LENGTH = 128  # bounds the work of hashing whatever a client sends


class PasswordField(serializers.CharField):
    """A password: kept exactly as typed (no whitespace trimming) and never echoed back."""

    def __init__(self, **kwargs):
        kwargs.setdefault('max_length', MAX_PASSWORD_LENGTH)
        super().__init__(trim_whitespace=False, write_only=True, **kwargs)


# --- requests -------------------------------------------------------------------------------


class SignUpSerializer(RequestSerializer):
    name = serializers.CharField(max_length=255)
    email = serializers.EmailField(max_length=254)
    password = PasswordField()


class LoginSerializer(RequestSerializer):
    email = serializers.EmailField(max_length=254)
    password = PasswordField()
    remember_me = serializers.BooleanField(default=False)


class RefreshSerializer(RequestSerializer):
    refresh_token = serializers.CharField()


class ForgotPasswordSerializer(RequestSerializer):
    email = serializers.EmailField(max_length=254)


class ResetPasswordSerializer(RequestSerializer):
    token = serializers.CharField()
    new_password = PasswordField()


class VerifyEmailSerializer(RequestSerializer):
    token = serializers.CharField()


# --- responses ------------------------------------------------------------------------------


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'email', 'name', 'email_verified')
        read_only_fields = fields


class TokensSerializer(serializers.Serializer):
    access_token = serializers.CharField(source='access_token.value')
    refresh_token = serializers.CharField()
    token_type = serializers.SerializerMethodField()
    expires_in = serializers.IntegerField(source='access_token.expires_in')

    def get_token_type(self, result) -> str:
        return 'Bearer'


class AuthResultSerializer(serializers.Serializer):
    user = UserSerializer()
    tokens = TokensSerializer(source='*')
