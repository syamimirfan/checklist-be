from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.authentication.models import EmailVerification, PasswordReset, UserSession

from .base import PASSWORD, User


class AuthenticationAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser('root@example.com', 'Root', PASSWORD)
        cls.member = User.objects.create_user('alice@example.com', 'Alice', PASSWORD)
        expires_at = timezone.now() + timedelta(hours=1)
        cls.session = UserSession.objects.create(user=cls.member, refresh_token_hash='a' * 64, expires_at=expires_at)
        EmailVerification.objects.create(user=cls.member, token_hash='b' * 64, expires_at=expires_at)
        PasswordReset.objects.create(user=cls.member, token_hash='c' * 64, expires_at=expires_at)

    def setUp(self):
        self.client.force_login(self.admin)

    def test_every_table_is_listed_by_user(self):
        for name in ('usersession', 'emailverification', 'passwordreset'):
            with self.subTest(model=name):
                response = self.client.get(reverse(f'admin:authentication_{name}_changelist'))

                self.assertContains(response, 'alice@example.com')

    def test_digests_are_never_displayed(self):
        page = self.client.get(reverse('admin:authentication_usersession_change', args=[self.session.pk]))

        self.assertEqual(page.status_code, 200)
        self.assertNotContains(page, 'a' * 64)

    def test_rows_cannot_be_added_or_edited_by_hand(self):
        self.assertEqual(self.client.get(reverse('admin:authentication_usersession_add')).status_code, 403)

        response = self.client.post(
            reverse('admin:authentication_usersession_change', args=[self.session.pk]),
            {'ip_address': '10.0.0.1'},
        )

        self.assertEqual(response.status_code, 403)

    def test_deleting_a_session_signs_that_device_out(self):
        self.client.post(
            reverse('admin:authentication_usersession_delete', args=[self.session.pk]),
            {'post': 'yes'},
        )

        self.assertFalse(UserSession.objects.filter(pk=self.session.pk).exists())
