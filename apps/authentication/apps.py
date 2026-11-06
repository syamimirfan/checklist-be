from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    name = 'apps.authentication'
    label = 'authentication'

    def ready(self):
        from . import docs  # noqa: F401  (registers the Swagger security scheme)
