from django.core import mail

from apps.authentication.models import EmailVerification, UserSession
from apps.authentication.services import AccessTokenService

from .base import PASSWORD, AuthAPITestCase, User

SIGNUP = 'authentication:signup'


class SignUpTests(AuthAPITestCase):
    payload = {'name': 'Alice Morgan', 'email': 'alice@example.com', 'password': PASSWORD}

    def test_creates_the_account_and_signs_it_in(self):
        response = self.post(SIGNUP, self.payload, HTTP_USER_AGENT='UnitTest/1.0')

        self.assertEqual(response.status_code, 201)
        body = response.json()
        user = User.objects.get(email='alice@example.com')
        self.assertEqual(
            body['user'],
            {'id': str(user.id), 'email': 'alice@example.com', 'name': 'Alice Morgan', 'email_verified': False},
        )
        self.assertEqual(body['tokens']['token_type'], 'Bearer')
        self.assertEqual(body['tokens']['expires_in'], 900)
        claims = AccessTokenService().decode(body['tokens']['access_token'])
        self.assertEqual(claims.user_id, str(user.id))

        session = UserSession.objects.get(user=user)
        self.assertEqual(claims.session_id, str(session.id))
        self.assertEqual(session.user_agent, 'UnitTest/1.0')
        self.assertEqual(session.ip_address, '127.0.0.1')

    def test_the_password_is_hashed_and_never_returned(self):
        response = self.post(SIGNUP, self.payload)

        self.assertNotIn(PASSWORD, response.content.decode())
        user = User.objects.get(email='alice@example.com')
        self.assertNotEqual(user.password, PASSWORD)
        self.assertTrue(user.check_password(PASSWORD))

    def test_email_is_stored_in_lowercase(self):
        self.post(SIGNUP, {**self.payload, 'email': 'Alice@Example.COM'})

        self.assertTrue(User.objects.filter(email='alice@example.com').exists())

    def test_sends_a_verification_email(self):
        self.post(SIGNUP, self.payload)

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, ['alice@example.com'])
        self.assertIn('http://localhost:3000/verify-email?token=', message.body)
        self.assertEqual(EmailVerification.objects.count(), 1)

    def test_rejects_an_email_that_is_already_registered(self):
        self.create_user()

        response = self.post(SIGNUP, {**self.payload, 'email': 'ALICE@example.com'})

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json()['error'],
            {
                'code': 'email_already_registered',
                'message': 'An account with this email already exists.',
                'fields': {},
            },
        )
        self.assertEqual(User.objects.count(), 1)

    def test_rejects_a_weak_password(self):
        for password in ('short1', 'password', '12345678', 'alice@example.com'):
            with self.subTest(password=password):
                response = self.post(SIGNUP, {**self.payload, 'password': password})

                self.assertEqual(response.status_code, 400)
                error = response.json()['error']
                self.assertEqual(error['code'], 'weak_password')
                self.assertTrue(error['fields']['password'])
        self.assertFalse(User.objects.exists())

    def test_rejects_a_password_that_contains_the_users_name(self):
        response = self.post(SIGNUP, {**self.payload, 'name': 'Alexander', 'password': 'alexander'})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error']['code'], 'weak_password')

    def test_reports_every_invalid_field(self):
        response = self.post(SIGNUP, {'name': '', 'email': 'not-an-email'})

        self.assertEqual(response.status_code, 400)
        error = response.json()['error']
        self.assertEqual(error['code'], 'validation_error')
        self.assertEqual(set(error['fields']), {'name', 'email', 'password'})
        self.assertEqual(error['fields']['email'], ['Enter a valid email address.'])
        self.assertEqual(error['message'], error['fields']['name'][0])  # `message` is the first one

    def test_a_failed_signup_does_not_send_email_or_create_a_session(self):
        self.create_user()

        self.post(SIGNUP, self.payload)

        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(UserSession.objects.count(), 0)
