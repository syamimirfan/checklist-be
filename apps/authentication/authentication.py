from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from .exceptions import InvalidAccessTokenError
from .models import UserSession
from .services import AccessTokenService


class JWTAuthentication(BaseAuthentication):
    """Authenticates a request from its `Authorization: Bearer <access token>` header.

    On success `request.user` is the user and `request.auth` is the `UserSession` the token belongs
    to. The session is looked up on every request, so logging out (or resetting a password) cuts
    off the access token straight away instead of when it expires.
    """

    keyword = 'Bearer'
    access_tokens = AccessTokenService()

    def authenticate(self, request):
        token = self._read_token(request)
        if token is None:
            return None  # no credentials sent: let the permission classes decide

        try:
            claims = self.access_tokens.decode(token)
        except InvalidAccessTokenError as error:
            raise AuthenticationFailed(error.message) from error

        session = (
            UserSession.objects.select_related('user')
            .filter(pk=claims.session_id, user_id=claims.user_id)
            .first()
        )
        if session is None or session.is_expired or not session.user.is_active:
            raise AuthenticationFailed(InvalidAccessTokenError.message)
        return session.user, session

    def authenticate_header(self, request):
        return self.keyword

    def _read_token(self, request):
        parts = get_authorization_header(request).split()
        if not parts or parts[0].lower() != self.keyword.lower().encode():
            return None
        if len(parts) != 2:
            raise AuthenticationFailed('Invalid Authorization header.')
        try:
            return parts[1].decode()
        except UnicodeError as error:
            raise AuthenticationFailed('Invalid Authorization header.') from error
