"""Thin HTTP layer: validate the body, call one service method, shape the reply.

Everything that is a business rule lives in `apps.authentication.services`.
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.views import PublicAPIView

from . import docs
from .serializers import (
    AuthResultSerializer,
    ForgotPasswordSerializer,
    LoginSerializer,
    RefreshSerializer,
    ResetPasswordSerializer,
    SignUpSerializer,
    UserSerializer,
    VerifyEmailSerializer,
)
from .services import AuthService, ClientInfo, EmailVerificationService, PasswordResetService


class SignUpView(PublicAPIView):
    """POST /api/auth/signup/ — create an account and sign it in."""

    throttle_scope = 'signup'
    service = AuthService()

    @docs.sign_up
    def post(self, request):
        data = SignUpSerializer.validated(request.data)
        result = self.service.sign_up(
            name=data['name'],
            email=data['email'],
            password=data['password'],
            client=ClientInfo.from_request(request),
        )
        return Response(AuthResultSerializer(result).data, status=status.HTTP_201_CREATED)


class LoginView(PublicAPIView):
    """POST /api/auth/login/ — exchange an email and password for tokens."""

    throttle_scope = 'login'
    service = AuthService()

    @docs.log_in
    def post(self, request):
        data = LoginSerializer.validated(request.data)
        result = self.service.log_in(
            email=data['email'],
            password=data['password'],
            remember_me=data['remember_me'],
            client=ClientInfo.from_request(request),
        )
        return Response(AuthResultSerializer(result).data)


class RefreshView(PublicAPIView):
    """POST /api/auth/refresh/ — trade a refresh token for a new access token and refresh token."""

    service = AuthService()

    @docs.refresh
    def post(self, request):
        data = RefreshSerializer.validated(request.data)
        result = self.service.refresh(data['refresh_token'])
        return Response(AuthResultSerializer(result).data)


class LogoutView(APIView):
    """POST /api/auth/logout/ — end the session the access token belongs to."""

    service = AuthService()

    @docs.log_out
    def post(self, request):
        self.service.log_out(request.auth)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    """GET /api/auth/me/ — the signed-in user."""

    @docs.me
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class ForgotPasswordView(PublicAPIView):
    """POST /api/auth/forgot-password/ — email a reset link. Always answers 204, whether or not the address has an account."""

    throttle_scope = 'password_reset'
    service = PasswordResetService()

    @docs.forgot_password
    def post(self, request):
        data = ForgotPasswordSerializer.validated(request.data)
        self.service.request(data['email'])
        return Response(status=status.HTTP_204_NO_CONTENT)


class ResetPasswordView(PublicAPIView):
    """POST /api/auth/reset-password/ — set a new password using the emailed token."""

    throttle_scope = 'password_reset'
    service = PasswordResetService()

    @docs.reset_password
    def post(self, request):
        data = ResetPasswordSerializer.validated(request.data)
        self.service.reset(data['token'], data['new_password'])
        return Response(status=status.HTTP_204_NO_CONTENT)


class VerifyEmailView(PublicAPIView):
    """POST /api/auth/verify-email/ — confirm an email address using the emailed token."""

    service = EmailVerificationService()

    @docs.verify_email
    def post(self, request):
        data = VerifyEmailSerializer.validated(request.data)
        self.service.verify(data['token'])
        return Response(status=status.HTTP_204_NO_CONTENT)
