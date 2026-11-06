from datetime import timedelta

from django.core import mail
from django.utils import timezone

from apps.authentication.models import EmailVerification

from .base import PASSWORD, AuthAPITestCase, User

SIGNUP = 'authentication:signup'
VERIFY = 'authentication:verify-email'


class VerifyEmailTests(AuthAPITestCase):
    def setUp(self):
        super().setUp()
        self.post(SIGNUP, {'name': 'Alice Morgan', 'email': 'alice@example.com', 'password': PASSWORD})
        self.token = self.emailed_token()
        self.user = User.objects.get(email='alice@example.com')

    def test_confirms_the_email_address(self):
        self.assertFalse(self.user.email_verified)

        response = self.post(VERIFY, {'token': self.token})

        self.assertEqual(response.status_code, 204)
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)
        self.assertIsNotNone(EmailVerification.objects.get().used_at)

    def test_the_link_works_only_once(self):
        self.post(VERIFY, {'token': self.token})

        again = self.post(VERIFY, {'token': self.token})

        self.assertEqual(again.status_code, 400)
        self.assertEqual(
            again.json()['error'],
            {
                'code': 'invalid_verification_link',
                'message': 'This verification link is invalid or has expired.',
                'fields': {},
            },
        )

    def test_rejects_an_unknown_token(self):
        response = self.post(VERIFY, {'token': 'made-up-token'})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error']['code'], 'invalid_verification_link')
        self.user.refresh_from_db()
        self.assertFalse(self.user.email_verified)

    def test_rejects_an_expired_token(self):
        EmailVerification.objects.update(expires_at=timezone.now() - timedelta(seconds=1))

        response = self.post(VERIFY, {'token': self.token})

        self.assertEqual(response.status_code, 400)
        self.user.refresh_from_db()
        self.assertFalse(self.user.email_verified)

    def test_a_password_reset_token_cannot_verify_an_email(self):
        mail.outbox.clear()
        self.post('authentication:forgot-password', {'email': 'alice@example.com'})
        reset_token = self.emailed_token()

        response = self.post(VERIFY, {'token': reset_token})

        self.assertEqual(response.status_code, 400)

    def test_requires_a_token(self):
        self.assertEqual(self.post(VERIFY, {}).status_code, 400)
