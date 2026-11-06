import logging
from urllib.parse import urlencode

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.timesince import timesince

logger = logging.getLogger(__name__)


class AuthMailer:
    """Sends the account emails, with links that point at the frontend.

    A failed send is logged but never raised: the account change that triggered the email has
    already happened, and for password resets an error would reveal that the address has an account.
    """

    def send_verification_email(self, user, token):
        link = self._frontend_link('/verify-email', token)
        self._send(
            user,
            subject='Verify your email address',
            body=(
                f'Hi {user.name},\n\n'
                f'Welcome to Checklist! Confirm your email address by opening this link:\n\n{link}\n\n'
                f'The link works once and expires in {self._expiry(settings.AUTH_EMAIL_VERIFICATION_LIFETIME)}.'
            ),
        )

    def send_password_reset_email(self, user, token):
        link = self._frontend_link('/reset-password', token)
        self._send(
            user,
            subject='Reset your password',
            body=(
                f'Hi {user.name},\n\n'
                f'Someone asked to reset the password for your Checklist account. '
                f'To choose a new one, open this link:\n\n{link}\n\n'
                f'The link works once and expires in {self._expiry(settings.AUTH_PASSWORD_RESET_LIFETIME)}. '
                f'If this wasn\'t you, you can ignore this email.'
            ),
        )

    def _send(self, user, *, subject, body):
        try:
            send_mail(subject, body, None, [user.email])
        except Exception:  # any mail backend error: see the class docstring
            logger.exception('Could not send the "%s" email to user %s', subject, user.pk)

    def _frontend_link(self, path, token):
        return f'{settings.FRONTEND_URL.rstrip("/")}{path}?{urlencode({"token": token})}'

    def _expiry(self, lifetime):
        start = timezone.now()
        return timesince(start, start + lifetime, depth=1)
