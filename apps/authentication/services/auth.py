from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.contrib.auth import authenticate, get_user_model
from django.db import IntegrityError, transaction

from apps.authentication.exceptions import EmailAlreadyRegisteredError, InvalidCredentialsError
from apps.authentication.passwords import validate_new_password

from .access_tokens import AccessToken, AccessTokenService
from .email_verification import EmailVerificationService
from .sessions import ClientInfo, SessionService

if TYPE_CHECKING:
    from apps.users.models import User


@dataclass(frozen=True)
class AuthResult:
    """What a successful sign-up, login or refresh hands back."""

    user: 'User'
    access_token: AccessToken
    refresh_token: str


class AuthService:
    """The account use cases: sign up, log in, renew a session, log out.

    The collaborators can be passed in (handy for tests); by default each one is built for you.
    """

    def __init__(self, sessions=None, access_tokens=None, email_verification=None):
        self.sessions = sessions or SessionService()
        self.access_tokens = access_tokens or AccessTokenService()
        self.email_verification = email_verification or EmailVerificationService()

    def sign_up(self, *, name, email, password, client=ClientInfo()):
        User = get_user_model()
        validate_new_password(password, User(email=email, name=name))

        try:
            with transaction.atomic():
                user = User.objects.create_user(email, name, password)
        except IntegrityError as error:  # the email is taken (the `unique` constraint on `users.email`)
            raise EmailAlreadyRegisteredError() from error

        self.email_verification.send(user)
        return self._start_session(user, remember_me=False, client=client)

    def log_in(self, *, email, password, remember_me=False, client=ClientInfo()):
        user = authenticate(username=email, password=password)
        if user is None:  # unknown email, wrong password or inactive account: deliberately indistinguishable
            raise InvalidCredentialsError()

        user.record_login()
        return self._start_session(user, remember_me=remember_me, client=client)

    def refresh(self, refresh_token):
        issued = self.sessions.rotate(refresh_token)
        return AuthResult(
            user=issued.session.user,
            access_token=self.access_tokens.issue(issued.session),
            refresh_token=issued.refresh_token,
        )

    def log_out(self, session):
        self.sessions.end(session)

    def _start_session(self, user, *, remember_me, client):
        issued = self.sessions.start(user, remember_me=remember_me, client=client)
        return AuthResult(
            user=user,
            access_token=self.access_tokens.issue(issued.session),
            refresh_token=issued.refresh_token,
        )
