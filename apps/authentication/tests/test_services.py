"""The services on their own, without HTTP: swapping collaborators in and the guarantees they make."""

from datetime import timedelta
from smtplib import SMTPException
from unittest import mock

from django.test import TestCase
from django.utils import timezone

from apps.authentication.models import EmailVerification, OneTimeToken, PasswordReset
from apps.authentication.services import (
    AuthService,
    EmailVerificationService,
    OneTimeTokenService,
    PasswordResetService,
)

from .base import PASSWORD, User


class FakeMailer:
    """Stands in for `AuthMailer` and just remembers what it was asked to send."""

    def __init__(self):
        self.verification_emails = []
        self.reset_emails = []

    def send_verification_email(self, user, token):
        self.verification_emails.append((user, token))

    def send_password_reset_email(self, user, token):
        self.reset_emails.append((user, token))


class AuthServiceTests(TestCase):
    def test_collaborators_can_be_swapped_for_fakes(self):
        mailer = FakeMailer()
        service = AuthService(email_verification=EmailVerificationService(mailer=mailer))

        result = service.sign_up(name='Alice Morgan', email='alice@example.com', password=PASSWORD)

        self.assertEqual(result.user.email, 'alice@example.com')
        [(emailed_user, token)] = mailer.verification_emails
        self.assertEqual(emailed_user, result.user)
        self.assertTrue(token)

    def test_a_mail_failure_does_not_undo_the_signup(self):
        service = AuthService()

        with mock.patch('apps.authentication.services.mailer.send_mail', side_effect=SMTPException('down')):
            with self.assertLogs('apps.authentication.services.mailer', level='ERROR'):
                result = service.sign_up(name='Alice Morgan', email='alice@example.com', password=PASSWORD)

        self.assertTrue(User.objects.filter(pk=result.user.pk).exists())
        self.assertTrue(result.refresh_token)


class OneTimeTokenServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('alice@example.com', 'Alice Morgan', PASSWORD)

    def test_the_base_class_cannot_be_used_directly(self):
        with self.assertRaises(TypeError):
            OneTimeTokenService()

    def test_subclasses_share_the_same_behaviour_with_their_own_table(self):
        for service, model in (
            (EmailVerificationService(mailer=FakeMailer()), EmailVerification),
            (PasswordResetService(mailer=FakeMailer()), PasswordReset),
        ):
            with self.subTest(service=type(service).__name__):
                token = service.issue(self.user)

                self.assertEqual(model.objects.filter(user=self.user).count(), 1)
                self.assertEqual(service.redeem(token), self.user)
                self.assertIsNotNone(model.objects.get(user=self.user).used_at)

    def test_a_token_cannot_be_redeemed_twice(self):
        service = PasswordResetService(mailer=FakeMailer())
        token = service.issue(self.user)
        service.redeem(token)

        with self.assertRaises(service.invalid_error):
            service.redeem(token)

    def test_a_token_from_one_service_is_unknown_to_the_other(self):
        token = PasswordResetService(mailer=FakeMailer()).issue(self.user)

        with self.assertRaises(EmailVerificationService.invalid_error):
            EmailVerificationService(mailer=FakeMailer()).redeem(token)


class OneTimeTokenModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('alice@example.com', 'Alice Morgan', PASSWORD)

    def make(self, **overrides):
        values = {'user': self.user, 'token_hash': 'x' * 64, 'expires_at': timezone.now() + timedelta(hours=1)}
        return PasswordReset.objects.create(**{**values, **overrides})

    def test_is_usable_until_it_is_used_or_expires(self):
        self.assertTrue(self.make().is_usable)

    def test_a_used_token_is_not_usable(self):
        token = self.make()
        token.mark_used()

        self.assertFalse(token.is_usable)

    def test_an_expired_token_is_not_usable(self):
        token = self.make(expires_at=timezone.now() - timedelta(seconds=1))

        self.assertFalse(token.is_usable)

    def test_both_token_tables_share_one_abstract_base(self):
        self.assertTrue(issubclass(EmailVerification, OneTimeToken))
        self.assertTrue(issubclass(PasswordReset, OneTimeToken))
        self.assertTrue(OneTimeToken._meta.abstract)
