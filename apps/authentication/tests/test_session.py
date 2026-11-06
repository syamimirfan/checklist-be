"""Staying signed in: the access token (`me`), renewing it (`refresh`) and ending the session (`logout`)."""

from datetime import timedelta

import jwt
from django.test import override_settings
from django.utils import timezone

from apps.authentication.models import UserSession

from .base import AuthAPITestCase

ME = 'authentication:me'
REFRESH = 'authentication:refresh'
LOGOUT = 'authentication:logout'


class MeTests(AuthAPITestCase):
    def setUp(self):
        super().setUp()
        self.user = self.create_user()

    def test_returns_the_signed_in_user(self):
        self.sign_in_as(self.user)

        response = self.get(ME)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {'id': str(self.user.id), 'email': 'alice@example.com', 'name': 'Alice Morgan', 'email_verified': False},
        )

    def test_requires_a_token(self):
        response = self.get(ME)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error']['code'], 'not_authenticated')
        self.assertEqual(response['WWW-Authenticate'], 'Bearer')

    def test_rejects_an_invalid_token(self):
        for header in ('Bearer not-a-jwt', 'Bearer', 'Bearer a b', 'Token abc'):
            with self.subTest(header=header):
                self.client.credentials(HTTP_AUTHORIZATION=header)

                response = self.get(ME)

                self.assertEqual(response.status_code, 401)
                self.assertEqual(response['WWW-Authenticate'], 'Bearer')

    def test_rejects_an_expired_token(self):
        with override_settings(AUTH_ACCESS_TOKEN_LIFETIME=timedelta(seconds=-5)):
            self.sign_in_as(self.user)

        response = self.get(ME)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error']['code'], 'authentication_failed')

    def test_rejects_a_token_signed_with_another_key(self):
        self.log_in()
        session = UserSession.objects.get(user=self.user)
        forged = self.forge_token(session, key='some-other-signing-key-that-is-long-enough')

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {forged}')

        self.assertEqual(self.get(ME).status_code, 401)

    def test_rejects_an_unsigned_token(self):
        self.log_in()
        session = UserSession.objects.get(user=self.user)
        payload = {'sub': str(self.user.id), 'sid': str(session.id), 'exp': timezone.now() + timedelta(hours=1)}
        unsigned = jwt.encode(payload, None, algorithm='none')

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {unsigned}')

        self.assertEqual(self.get(ME).status_code, 401)

    def test_stops_working_when_the_session_is_deleted(self):
        self.sign_in_as(self.user)
        UserSession.objects.all().delete()

        self.assertEqual(self.get(ME).status_code, 401)

    def test_stops_working_when_the_session_has_expired(self):
        self.sign_in_as(self.user)
        UserSession.objects.update(expires_at=timezone.now() - timedelta(seconds=1))

        self.assertEqual(self.get(ME).status_code, 401)

    def test_stops_working_for_a_deactivated_user(self):
        self.sign_in_as(self.user)
        self.user.is_active = False
        self.user.save()

        self.assertEqual(self.get(ME).status_code, 401)

    def forge_token(self, session, *, key):
        payload = {'sub': str(self.user.id), 'sid': str(session.id), 'exp': timezone.now() + timedelta(hours=1)}
        return jwt.encode(payload, key, algorithm='HS256')


class RefreshTests(AuthAPITestCase):
    def setUp(self):
        super().setUp()
        self.user = self.create_user()
        self.tokens = self.log_in().json()['tokens']

    def refresh(self, refresh_token):
        return self.post(REFRESH, {'refresh_token': refresh_token})

    def test_returns_new_tokens_for_the_same_user(self):
        response = self.refresh(self.tokens['refresh_token'])

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['user']['id'], str(self.user.id))
        self.assertNotEqual(body['tokens']['refresh_token'], self.tokens['refresh_token'])

    def test_the_new_access_token_works(self):
        body = self.refresh(self.tokens['refresh_token']).json()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {body["tokens"]["access_token"]}')

        self.assertEqual(self.get(ME).status_code, 200)

    def test_each_refresh_token_works_only_once(self):
        first = self.refresh(self.tokens['refresh_token']).json()['tokens']['refresh_token']

        reused = self.refresh(self.tokens['refresh_token'])
        renewed = self.refresh(first)

        self.assertEqual(reused.status_code, 401)
        self.assertEqual(reused.json()['error']['code'], 'invalid_refresh_token')
        self.assertEqual(renewed.status_code, 200)

    def test_keeps_one_session_and_does_not_extend_its_expiry(self):
        expires_at = UserSession.objects.get().expires_at

        self.refresh(self.tokens['refresh_token'])

        session = UserSession.objects.get()
        self.assertEqual(session.expires_at, expires_at)

    def test_the_stored_value_is_a_digest_not_the_token(self):
        refresh_token = self.refresh(self.tokens['refresh_token']).json()['tokens']['refresh_token']

        stored = UserSession.objects.get().refresh_token_hash

        self.assertNotEqual(stored, refresh_token)
        self.assertEqual(len(stored), 64)

    def test_rejects_an_unknown_token(self):
        self.assertEqual(self.refresh('made-up-token').status_code, 401)

    def test_rejects_an_expired_session(self):
        UserSession.objects.update(expires_at=timezone.now() - timedelta(seconds=1))

        self.assertEqual(self.refresh(self.tokens['refresh_token']).status_code, 401)

    def test_rejects_a_deactivated_user(self):
        self.user.is_active = False
        self.user.save()

        self.assertEqual(self.refresh(self.tokens['refresh_token']).status_code, 401)

    def test_requires_a_refresh_token(self):
        response = self.post(REFRESH, {})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error']['code'], 'validation_error')


class LogoutTests(AuthAPITestCase):
    def setUp(self):
        super().setUp()
        self.user = self.create_user()

    def test_ends_the_session_immediately(self):
        body = self.sign_in_as(self.user)

        response = self.post(LOGOUT)

        self.assertEqual(response.status_code, 204)
        self.assertFalse(UserSession.objects.exists())
        self.assertEqual(self.get(ME).status_code, 401)
        self.client.credentials()
        refresh = self.post(REFRESH, {'refresh_token': body['tokens']['refresh_token']})
        self.assertEqual(refresh.status_code, 401)

    def test_only_ends_the_current_device(self):
        self.log_in()  # another device
        self.sign_in_as(self.user)

        self.post(LOGOUT)

        self.assertEqual(UserSession.objects.filter(user=self.user).count(), 1)

    def test_requires_a_token(self):
        self.assertEqual(self.post(LOGOUT).status_code, 401)
