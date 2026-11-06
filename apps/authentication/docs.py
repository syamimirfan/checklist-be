"""What Swagger shows for the auth endpoints. The views apply these as decorators, e.g. `@docs.sign_up`.

Keeping the descriptions here leaves the views thin. Error entries come from the exception classes
in `exceptions.py`, so they match what the services actually raise.
"""

from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.utils import extend_schema

from apps.core.api_docs import THROTTLED, VALIDATION_FAILED, DocumentedError, error_responses

from .exceptions import (
    EmailAlreadyRegisteredError,
    InvalidAccessTokenError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    InvalidResetLinkError,
    InvalidVerificationLinkError,
    WeakPasswordError,
)
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

class JWTAuthenticationScheme(OpenApiAuthenticationExtension):
    """Describes the `Authorization: Bearer` header, which is what gives Swagger its Authorize button."""

    target_class = 'apps.authentication.authentication.JWTAuthentication'
    name = 'bearerAuth'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
            'description': 'The `access_token` from POST /api/auth/login/ (or signup, or refresh).',
        }


# Endpoints behind the Bearer token answer 401 when it is missing, or invalid or expired.
SIGN_IN_REQUIRED = (
    DocumentedError(401, 'not_authenticated', 'Authentication credentials were not provided.'),
    DocumentedError(401, 'authentication_failed', InvalidAccessTokenError.message),
)

sign_up = extend_schema(
    summary='Create an account',
    description='Creates the account, emails a verification link and signs the new user in.',
    request=SignUpSerializer,
    responses={
        201: AuthResultSerializer,
        **error_responses(
            VALIDATION_FAILED,
            DocumentedError.of(WeakPasswordError),
            DocumentedError.of(EmailAlreadyRegisteredError),
            THROTTLED,
        ),
    },
)

log_in = extend_schema(
    summary='Sign in',
    description=(
        'Exchanges an email and password for an access token and a refresh token. '
        'With `remember_me` the session lasts 30 days instead of 1.'
    ),
    request=LoginSerializer,
    responses={
        200: AuthResultSerializer,
        **error_responses(VALIDATION_FAILED, DocumentedError.of(InvalidCredentialsError), THROTTLED),
    },
)

refresh = extend_schema(
    summary='Refresh the tokens',
    description=(
        'Trades a refresh token for a new access token and a new refresh token. '
        'Each refresh token works once: the old one stops working as soon as it is used.'
    ),
    request=RefreshSerializer,
    responses={
        200: AuthResultSerializer,
        **error_responses(VALIDATION_FAILED, DocumentedError.of(InvalidRefreshTokenError)),
    },
)

log_out = extend_schema(
    summary='Sign out',
    description='Ends the session this access token belongs to. The tokens stop working immediately.',
    request=None,
    responses={204: None, **error_responses(*SIGN_IN_REQUIRED)},
)

me = extend_schema(
    summary='Get the signed-in user',
    responses={200: UserSerializer, **error_responses(*SIGN_IN_REQUIRED)},
)

forgot_password = extend_schema(
    summary='Email a password reset link',
    description=(
        'Always answers 204, whether or not the address has an account, so it cannot be used '
        'to find out who is registered.'
    ),
    request=ForgotPasswordSerializer,
    responses={204: None, **error_responses(VALIDATION_FAILED, THROTTLED)},
)

reset_password = extend_schema(
    summary='Set a new password',
    description=(
        'Uses the token from the emailed link, which works once. '
        'Every session of the account is signed out afterwards.'
    ),
    request=ResetPasswordSerializer,
    responses={
        204: None,
        **error_responses(
            VALIDATION_FAILED,
            DocumentedError.of(WeakPasswordError),
            DocumentedError.of(InvalidResetLinkError),
            THROTTLED,
        ),
    },
)

verify_email = extend_schema(
    summary='Confirm an email address',
    description='Uses the token from the emailed link, which works once.',
    request=VerifyEmailSerializer,
    responses={
        204: None,
        **error_responses(VALIDATION_FAILED, DocumentedError.of(InvalidVerificationLinkError)),
    },
)
