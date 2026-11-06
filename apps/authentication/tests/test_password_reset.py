from datetime import timedelta

from django.core import mail
from django.utils import timezone

from apps.authentication.models import PasswordReset, UserSession

from .base import PASSWORD, AuthAPITestCase

FORGOT = 'authentication:forgot-password'
RESET = 'authentication:reset-password'

NEW_PASSWORD = 'another-strong-pass-2'


class ForgotPasswordTests(AuthAPITestCase):
    def setUp(self):
        super().setUp()
        self.user = self.create_user()

    def test_emails_a_reset_link(self):
        response = self.post(FORGOT, {'email': 'alice@example.com'})

        self.assertEqual(response.status_code, 204)
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, ['alice@example.com'])
        self.assertIn('http://localhost:3000/reset-password?token=', message.body)
        self.assertIn('expires in 1\xa0hour', message.body)  # Django joins number and unit with a no-break space

    def test_only_the_digest_of_the_token_is_stored(self):
        self.post(FORGOT, {'email': 'alice@example.com'})

        token = self.emailed_token()

        self.assertNotEqual(PasswordReset.objects.get().token_hash, token)

    def test_answers_the_same_for_an_unknown_email_and_sends_nothing(self):
        known = self.post(FORGOT, {'email': 'alice@example.com'})
        mail.outbox.clear()

        unknown = self.post(FORGOT, {'email': 'nobody@example.com'})

        self.assertEqual(unknown.status_code, known.status_code)
        self.assertEqual(unknown.content, known.content)
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(PasswordReset.objects.count(), 1)

    def test_ignores_email_case(self):
        self.post(FORGOT, {'email': 'ALICE@Example.com'})

        self.assertEqual(len(mail.outbox), 1)

    def test_sends_nothing_to_a_deactivated_account(self):
        self.user.is_active = False
        self.user.save()

        self.post(FORGOT, {'email': 'alice@example.com'})

        self.assertEqual(len(mail.outbox), 0)

    def test_a_newer_link_replaces_the_older_one(self):
        self.post(FORGOT, {'email': 'alice@example.com'})
        old_token = self.emailed_token()
        self.post(FORGOT, {'email': 'alice@example.com'})

        response = self.post(RESET, {'token': old_token, 'new_password': NEW_PASSWORD})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(PasswordReset.objects.count(), 1)

    def test_rejects_an_invalid_email(self):
        response = self.post(FORGOT, {'email': 'nope'})

        self.assertEqual(response.status_code, 400)

    def test_is_rate_limited(self):
        for _ in range(5):
            self.post(FORGOT, {'email': 'alice@example.com'})

        self.assertEqual(self.post(FORGOT, {'email': 'alice@example.com'}).status_code, 429)


class ResetPasswordTests(AuthAPITestCase):
    def setUp(self):
        super().setUp()
        self.user = self.create_user()
        self.post(FORGOT, {'email': 'alice@example.com'})
        self.token = self.emailed_token()

    def reset(self, token=None, new_password=NEW_PASSWORD):
        return self.post(RESET, {'token': token or self.token, 'new_password': new_password})

    def test_sets_the_new_password(self):
        response = self.reset()

        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.log_in(password=NEW_PASSWORD).status_code, 200)
        self.assertEqual(self.log_in(password=PASSWORD).status_code, 401)

    def test_signs_the_user_out_everywhere(self):
        self.log_in()
        self.log_in()
        self.assertEqual(UserSession.objects.count(), 2)

        self.reset()

        self.assertFalse(UserSession.objects.filter(user=self.user).exists())

    def test_the_link_works_only_once(self):
        self.reset()

        again = self.reset(new_password='yet-another-pass-3')

        self.assertEqual(again.status_code, 400)
        self.assertEqual(
            again.json()['error'],
            {'code': 'invalid_reset_link', 'message': 'This reset link is invalid or has expired.', 'fields': {}},
        )
        self.assertEqual(self.log_in(password=NEW_PASSWORD).status_code, 200)

    def test_rejects_an_unknown_token(self):
        response = self.reset(token='made-up-token')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error']['code'], 'invalid_reset_link')

    def test_rejects_an_expired_token(self):
        PasswordReset.objects.update(expires_at=timezone.now() - timedelta(seconds=1))

        response = self.reset()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error']['code'], 'invalid_reset_link')
        self.assertEqual(self.log_in(password=PASSWORD).status_code, 200)

    def test_rejects_a_weak_password_and_keeps_the_link_usable(self):
        weak = self.reset(new_password='short')

        self.assertEqual(weak.status_code, 400)
        error = weak.json()['error']
        self.assertEqual(error['code'], 'weak_password')
        self.assertTrue(error['fields']['new_password'])
        self.assertEqual(self.log_in(password=PASSWORD).status_code, 200)  # unchanged
        self.assertEqual(self.reset().status_code, 204)  # the same link still works

    def test_rejects_a_password_similar_to_the_account_details(self):
        response = self.reset(new_password='alice@example.com')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error']['code'], 'weak_password')

    def test_requires_a_token_and_a_password(self):
        response = self.post(RESET, {})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(set(response.json()['error']['fields']), {'token', 'new_password'})
