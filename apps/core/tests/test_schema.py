from django.conf import settings
from django.db import connection
from django.test import TestCase

from apps.core.apps import create_schema


class SchemaTests(TestCase):
    def test_connection_uses_configured_schema(self):
        with connection.cursor() as cursor:
            cursor.execute('SELECT current_schema()')
            self.assertEqual(cursor.fetchone()[0], settings.DB_SCHEMA)

    def test_tables_are_created_in_configured_schema(self):
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT 1 FROM information_schema.tables WHERE table_schema = %s AND table_name = %s',
                [settings.DB_SCHEMA, 'users'],
            )
            self.assertIsNotNone(cursor.fetchone())

    def test_create_schema_is_safe_to_repeat(self):
        create_schema(using='default')
        create_schema(using='default')
