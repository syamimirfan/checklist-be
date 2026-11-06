import re

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

User = get_user_model()

PASSWORD = 'a-strong-pass-1'


class AuthAPITestCase(TestCase):
    """Base for the endpoint tests: a JSON API client and a clean throttle counter for every test."""

    client_class = APIClient

    def setUp(self):
        cache.clear()  # DRF keeps its throttle counters in the cache

    # --- setup helpers -------------------------------------------------------------------

    def create_user(self, email='alice@example.com', name='Alice Morgan', password=PASSWORD, **extra):
        return User.objects.create_user(email, name, password, **extra)

    def log_in(self, email='alice@example.com', password=PASSWORD, **extra):
        """POST to the login endpoint and return the response."""
        return self.post('authentication:login', {'email': email, 'password': password, **extra})

    def sign_in_as(self, user):
        """Log in as `user` and send the access token with every following request. Returns the login body."""
        body = self.log_in(email=user.email).json()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {body["tokens"]["access_token"]}')
        return body

    # --- request helpers -----------------------------------------------------------------

    def post(self, url_name, data=None, **extra):
        return self.client.post(reverse(url_name), data or {}, format='json', **extra)

    def get(self, url_name, **extra):
        return self.client.get(reverse(url_name), **extra)

    # --- email helpers -------------------------------------------------------------------

    def emailed_token(self, message=None):
        """The `token=...` value from the link in an email (the latest one by default)."""
        message = message or mail.outbox[-1]
        return re.search(r'token=([\w-]+)', message.body).group(1)
