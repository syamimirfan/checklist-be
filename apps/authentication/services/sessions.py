from dataclasses import dataclass

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.authentication.exceptions import InvalidRefreshTokenError
from apps.authentication.models import UserSession
from apps.authentication.opaque_tokens import generate_opaque_token, hash_opaque_token


@dataclass(frozen=True)
class ClientInfo:
    """Who is calling. Recorded on the session so a user can recognise their devices."""

    user_agent: str = ''
    ip_address: str | None = None

    @classmethod
    def from_request(cls, request):
        return cls(
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            ip_address=request.META.get('REMOTE_ADDR') or None,
        )


@dataclass(frozen=True)
class IssuedSession:
    session: UserSession
    refresh_token: str  # the raw token; only its digest is stored, so this is the one chance to hand it out


class SessionService:
    """Starts, renews and ends sessions (the `sessions` table)."""

    def start(self, user, *, remember_me=False, client=ClientInfo()):
        refresh_token = generate_opaque_token()
        session = UserSession.objects.create(
            user=user,
            refresh_token_hash=hash_opaque_token(refresh_token),
            user_agent=client.user_agent[:255],
            ip_address=client.ip_address,
            expires_at=timezone.now() + self._lifetime(remember_me),
        )
        return IssuedSession(session=session, refresh_token=refresh_token)

    def rotate(self, refresh_token):
        """Swap a refresh token for a fresh one. The old token stops working, the session's expiry stays."""
        with transaction.atomic():
            session = (
                UserSession.objects.select_for_update(of=('self',))
                .select_related('user')
                .filter(refresh_token_hash=hash_opaque_token(refresh_token))
                .first()
            )
            if session is None or session.is_expired or not session.user.is_active:
                raise InvalidRefreshTokenError()

            new_refresh_token = generate_opaque_token()
            session.refresh_token_hash = hash_opaque_token(new_refresh_token)
            session.save(update_fields=['refresh_token_hash'])
        return IssuedSession(session=session, refresh_token=new_refresh_token)

    def end(self, session):
        session.delete()

    def end_all(self, user):
        UserSession.objects.filter(user=user).delete()

    def _lifetime(self, remember_me):
        if remember_me:
            return settings.AUTH_REMEMBER_ME_LIFETIME
        return settings.AUTH_REFRESH_TOKEN_LIFETIME
