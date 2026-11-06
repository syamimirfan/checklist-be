from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class UserAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser('root@example.com', 'Root', 'a-strong-pass-1')
        cls.member = User.objects.create_user('alice@example.com', 'Alice', 'a-strong-pass-1')

    def setUp(self):
        self.client.force_login(self.admin)

    def test_login_page_with_email(self):
        self.client.logout()
        response = self.client.post(
            reverse('admin:login'),
            {'username': 'root@example.com', 'password': 'a-strong-pass-1', 'next': reverse('admin:index')},
        )
        self.assertRedirects(response, reverse('admin:index'))

    def test_changelist(self):
        response = self.client.get(reverse('admin:users_user_changelist'))
        self.assertContains(response, 'alice@example.com')

    def test_change_page(self):
        response = self.client.get(reverse('admin:users_user_change', args=[self.member.pk]))
        self.assertEqual(response.status_code, 200)

    def test_add_user(self):
        response = self.client.post(
            reverse('admin:users_user_add'),
            {
                'email': 'Bob@Example.com',
                'name': 'Bob',
                'usable_password': 'true',
                'password1': 'another-strong-pass-2',
                'password2': 'another-strong-pass-2',
            },
        )
        self.assertEqual(response.status_code, 302)
        bob = User.objects.get(email='bob@example.com')
        self.assertEqual(bob.name, 'Bob')
        self.assertTrue(bob.check_password('another-strong-pass-2'))
