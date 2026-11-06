from django.conf import settings
from django.db import transaction

from apps.authentication.exceptions import InvalidVerificationLinkError
from apps.authentication.models import EmailVerification

from .mailer import AuthMailer
from .one_time_tokens import OneTimeTokenService


class EmailVerificationService(OneTimeTokenService):
    """Confirms that a user owns the email address they signed up with."""

    model = EmailVerification
    invalid_error = InvalidVerificationLinkError

    def __init__(self, mailer=None):
        self.mailer = mailer or AuthMailer()

    @property
    def lifetime(self):
        return settings.AUTH_EMAIL_VERIFICATION_LIFETIME

    def send(self, user):
        self.mailer.send_verification_email(user, self.issue(user))

    def verify(self, token):
        with transaction.atomic():
            user = self.redeem(token)
            user.mark_email_verified()
