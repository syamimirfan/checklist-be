from dataclasses import dataclass

import jwt
from django.conf import settings
from django.utils import timezone

from apps.authentication.exceptions import InvalidAccessTokenError


@dataclass(frozen=True)
class AccessToken:
    value: str
    expires_in: int  # seconds


@dataclass(frozen=True)
class AccessTokenClaims:
    user_id: str
    session_id: str


class AccessTokenService:
    """Issues and reads the short-lived JWT that the client sends as `Authorization: Bearer <token>`.

    The token names the user (`sub`) and the session it belongs to (`sid`), so ending the session
    also ends the token's usefulness.
    """

    algorithm = 'HS256'
    required_claims = ('exp', 'sub', 'sid')

    def issue(self, session):
        now = timezone.now()
        lifetime = settings.AUTH_ACCESS_TOKEN_LIFETIME
        payload = {
            'sub': str(session.user_id),
            'sid': str(session.id),
            'iat': now,
            'exp': now + lifetime,
        }
        value = jwt.encode(payload, settings.SECRET_KEY, algorithm=self.algorithm)
        return AccessToken(value=value, expires_in=int(lifetime.total_seconds()))

    def decode(self, value):
        try:
            payload = jwt.decode(
                value,
                settings.SECRET_KEY,
                algorithms=[self.algorithm],
                options={'require': list(self.required_claims)},
            )
        except jwt.InvalidTokenError as error:
            raise InvalidAccessTokenError() from error
        return AccessTokenClaims(user_id=payload['sub'], session_id=payload['sid'])
