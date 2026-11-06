import uuid

from django.contrib.auth import authenticate, get_user_model
from django.db import IntegrityError, connection, transaction
from django.test import TestCase

User = get_user_model()


class UserManagerTests(TestCase):
    def test_create_user_defaults(self):
        user = User.objects.create_user('alice@example.com', 'Alice', 'a-strong-pass-1')

        self.assertIsInstance(user.id, uuid.UUID)
        self.assertEqual(user.email, 'alice@example.com')
        self.assertEqual(user.name, 'Alice')
        self.assertFalse(user.email_verified)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertIsNotNone(user.created_at)
        self.assertIsNotNone(user.updated_at)

    def test_password_is_hashed_into_password_hash_column(self):
        user = User.objects.create_user('alice@example.com', 'Alice', 'a-strong-pass-1')

        with connection.cursor() as cursor:
            cursor.execute('SELECT password_hash FROM users WHERE id = %s', [user.id])
            stored = cursor.fetchone()[0]
        self.assertNotEqual(stored, 'a-strong-pass-1')
        self.assertTrue(user.check_password('a-strong-pass-1'))

    def test_email_is_stored_lowercase(self):
        user = User.objects.create_user('  Alice@Example.COM ', 'Alice', 'a-strong-pass-1')
        self.assertEqual(User.objects.get(pk=user.pk).email, 'alice@example.com')

    def test_email_is_required(self):
        with self.assertRaisesMessage(ValueError, 'email address must be set'):
            User.objects.create_user('', 'Alice', 'a-strong-pass-1')

    def test_email_must_be_unique_ignoring_case(self):
        User.objects.create_user('alice@example.com', 'Alice', 'a-strong-pass-1')
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.create_user('ALICE@example.com', 'Alice 2', 'a-strong-pass-1')

    def test_create_superuser(self):
        user = User.objects.create_superuser('root@example.com', 'Root', 'a-strong-pass-1')

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.email_verified)

    def test_create_superuser_rejects_non_staff(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser('root@example.com', 'Root', 'a-strong-pass-1', is_staff=False)


class UserAuthTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('alice@example.com', 'Alice', 'a-strong-pass-1')

    def test_authenticate_with_email(self):
        self.assertEqual(authenticate(username='alice@example.com', password='a-strong-pass-1'), self.user)

    def test_authenticate_ignores_email_case(self):
        self.assertEqual(authenticate(username='Alice@Example.com', password='a-strong-pass-1'), self.user)

    def test_authenticate_rejects_wrong_password(self):
        self.assertIsNone(authenticate(username='alice@example.com', password='wrong'))

    def test_inactive_user_cannot_authenticate(self):
        self.user.is_active = False
        self.user.save()
        self.assertIsNone(authenticate(username='alice@example.com', password='a-strong-pass-1'))

    def test_str_is_email(self):
        self.assertEqual(str(self.user), 'alice@example.com')
