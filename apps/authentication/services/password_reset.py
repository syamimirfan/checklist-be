from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction

from apps.authentication.exceptions import InvalidResetLinkError
from apps.authentication.models import PasswordReset
from apps.authentication.passwords import validate_new_password

from .mailer import AuthMailer
from .one_time_tokens import OneTimeTokenService
from .sessions import SessionService


class PasswordResetService(OneTimeTokenService):
    """The forgot-password flow: email a link, then accept a new password with it."""

    model = PasswordReset
    invalid_error = InvalidResetLinkError

    def __init__(self, sessions=None, mailer=None):
        self.sessions = sessions or SessionService()
        self.mailer = mailer or AuthMailer()

    @property
    def lifetime(self):
        return settings.AUTH_PASSWORD_RESET_LIFETIME

    def request(self, email):
        """Email a reset link if `email` belongs to an active account, and do nothing otherwise.

        The caller gets the same result either way, so the endpoint can't be used to find out
        which addresses have an account.
        """
        User = get_user_model()
        user = User.objects.filter(email=email.strip().lower(), is_active=True).first()
        if user is not None:
            self.mailer.send_password_reset_email(user, self.issue(user))

    def reset(self, token, new_password):
        """Set a new password and sign the user out everywhere.

        If the password is rejected the token is not used up, so the same link can be tried again.
        """
        with transaction.atomic():
            user = self.redeem(token)
            validate_new_password(new_password, user, field='new_password')
            user.change_password(new_password)
            self.sessions.end_all(user)
