from datetime import timedelta

from django.utils import timezone

from apps.authentication.models import UserSession

from .base import AuthAPITestCase


class LoginTests(AuthAPITestCase):
    def setUp(self):
        super().setUp()
        self.user = self.create_user()

    def test_returns_the_user_and_tokens(self):
        response = self.log_in()

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['user']['email'], 'alice@example.com')
        self.assertEqual(body['user']['id'], str(self.user.id))
        self.assertTrue(body['tokens']['access_token'])
        self.assertTrue(body['tokens']['refresh_token'])
        self.assertEqual(UserSession.objects.filter(user=self.user).count(), 1)

    def test_records_the_last_login(self):
        self.assertIsNone(self.user.last_login)

        self.log_in()

        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.last_login)

    def test_ignores_email_case_and_surrounding_spaces(self):
        self.assertEqual(self.log_in(email='  Alice@Example.COM ').status_code, 200)

    def test_each_login_is_its_own_session(self):
        self.log_in()
        self.log_in()

        self.assertEqual(UserSession.objects.filter(user=self.user).count(), 2)

    def test_wrong_password_and_unknown_email_look_the_same(self):
        wrong_password = self.log_in(password='not-the-password')
        unknown_email = self.log_in(email='nobody@example.com')

        self.assertEqual(wrong_password.status_code, 401)
        self.assertEqual(wrong_password.json(), unknown_email.json())
        self.assertEqual(
            wrong_password.json()['error'],
            {'code': 'invalid_credentials', 'message': 'Invalid email or password.', 'fields': {}},
        )

    def test_inactive_accounts_cannot_log_in(self):
        self.user.is_active = False
        self.user.save()

        self.assertEqual(self.log_in().status_code, 401)

    def test_unverified_accounts_can_log_in(self):
        self.assertFalse(self.user.email_verified)

        self.assertEqual(self.log_in().status_code, 200)

    def test_a_normal_session_lasts_one_day(self):
        self.log_in()

        self.assertSessionLasts(timedelta(days=1))

    def test_remember_me_keeps_the_session_for_thirty_days(self):
        self.log_in(remember_me=True)

        self.assertSessionLasts(timedelta(days=30))

    def test_rejects_a_malformed_request(self):
        response = self.post('authentication:login', {'email': 'not-an-email'})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(set(response.json()['error']['fields']), {'email', 'password'})

    def test_is_rate_limited(self):
        for _ in range(10):
            self.log_in(password='wrong')

        response = self.log_in()  # even the right password is refused once the limit is hit

        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json()['error']['code'], 'throttled')
        self.assertIn('Retry-After', response)

    def assertSessionLasts(self, lifetime):
        session = UserSession.objects.get(user=self.user)
        remaining = session.expires_at - timezone.now()
        self.assertLess(abs(remaining - lifetime), timedelta(minutes=1))
