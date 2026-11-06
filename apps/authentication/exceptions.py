from http import HTTPStatus

from apps.core.exceptions import ApplicationError


class InvalidCredentialsError(ApplicationError):
    status_code = HTTPStatus.UNAUTHORIZED
    code = 'invalid_credentials'
    message = 'Invalid email or password.'


class EmailAlreadyRegisteredError(ApplicationError):
    status_code = HTTPStatus.CONFLICT
    code = 'email_already_registered'
    message = 'An account with this email already exists.'


class WeakPasswordError(ApplicationError):
    code = 'weak_password'
    message = 'This password is too weak.'


class InvalidAccessTokenError(ApplicationError):
    status_code = HTTPStatus.UNAUTHORIZED
    code = 'invalid_access_token'
    message = 'Your access token is invalid or has expired.'


class InvalidRefreshTokenError(ApplicationError):
    status_code = HTTPStatus.UNAUTHORIZED
    code = 'invalid_refresh_token'
    message = 'Your session has expired. Please sign in again.'


class InvalidResetLinkError(ApplicationError):
    code = 'invalid_reset_link'
    message = 'This reset link is invalid or has expired.'


class InvalidVerificationLinkError(ApplicationError):
    code = 'invalid_verification_link'
    message = 'This verification link is invalid or has expired.'
