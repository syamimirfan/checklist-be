from django.apps import AppConfig
from django.conf import settings
from django.db import connections
from django.db.models.signals import pre_migrate


def create_schema(using, **kwargs):
    """Create the PostgreSQL schema named by DB_SCHEMA before migrations run, if it is missing."""
    connection = connections[using]
    schema = getattr(settings, 'DB_SCHEMA', None)
    if connection.vendor != 'postgresql' or not schema:
        return

    with connection.cursor() as cursor:
        cursor.execute('SELECT 1 FROM pg_namespace WHERE nspname = %s', [schema])
        if cursor.fetchone() is None:
            cursor.execute(f'CREATE SCHEMA {connection.ops.quote_name(schema)}')


class CoreConfig(AppConfig):
    name = 'apps.core'
    label = 'core'

    def ready(self):
        pre_migrate.connect(create_schema, sender=self)
