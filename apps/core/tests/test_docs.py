from io import StringIO

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from apps.authentication.exceptions import EmailAlreadyRegisteredError, WeakPasswordError
from apps.core.api_docs import VALIDATION_FAILED, DocumentedError, error_responses
from apps.landing.error_messages import ERROR_COPY

ENDPOINTS = {
    ('/api/landing/', 'get'),
    ('/api/auth/signup/', 'post'),
    ('/api/auth/login/', 'post'),
    ('/api/auth/refresh/', 'post'),
    ('/api/auth/logout/', 'post'),
    ('/api/auth/me/', 'get'),
    ('/api/auth/forgot-password/', 'post'),
    ('/api/auth/reset-password/', 'post'),
    ('/api/auth/verify-email/', 'post'),
}


class ApiDocsTests(TestCase):
    def schema(self):
        response = self.client.get(reverse('schema'), {'format': 'json'})
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_the_schema_generates_without_warnings(self):
        # --fail-on-warn makes drf-spectacular raise for anything it could not describe.
        call_command('spectacular', '--validate', '--fail-on-warn', stdout=StringIO())

    def test_every_endpoint_is_documented_and_nothing_else(self):
        documented = {
            (path, method) for path, operations in self.schema()['paths'].items() for method in operations
        }

        self.assertEqual(documented, ENDPOINTS)

    def test_only_the_signed_in_endpoints_ask_for_the_bearer_token(self):
        paths = self.schema()['paths']

        for path in ('/api/auth/logout/', '/api/auth/me/'):
            with self.subTest(path=path):
                (operation,) = paths[path].values()
                self.assertEqual(operation['security'], [{'bearerAuth': []}])
        for path in ('/api/auth/signup/', '/api/auth/login/', '/api/landing/'):
            with self.subTest(path=path):
                (operation,) = paths[path].values()
                self.assertEqual(operation['security'], [{}])

    def test_the_bearer_scheme_is_described(self):
        scheme = self.schema()['components']['securitySchemes']['bearerAuth']

        self.assertEqual((scheme['type'], scheme['scheme'], scheme['bearerFormat']), ('http', 'bearer', 'JWT'))

    def test_errors_are_documented_with_the_codes_the_services_raise(self):
        signup = self.schema()['paths']['/api/auth/signup/']['post']['responses']

        self.assertEqual(
            signup['409']['content']['application/json']['examples']['EmailAlreadyRegistered']['value'],
            {
                'error': {
                    'code': EmailAlreadyRegisteredError.code,
                    'message': EmailAlreadyRegisteredError.message,
                    'fields': {},
                },
            },
        )
        self.assertEqual(set(signup), {'201', '400', '409', '429'})

    def test_the_landing_endpoint_documents_every_error_status_with_its_message(self):
        landing = self.schema()['paths']['/api/landing/']['get']['responses']

        self.assertEqual(set(landing), {'200', '401', '403', '404', '405', '406', '500'})
        for status, copy in ERROR_COPY.items():
            with self.subTest(status=status):
                (example,) = landing[str(status)]['content']['application/json']['examples'].values()
                self.assertEqual(
                    example['value'],
                    {'error': {'code': copy.code, 'message': copy.message, 'fields': {}}},
                )

    def test_the_landing_success_response_does_not_include_the_error_messages(self):
        landing_page = self.schema()['components']['schemas']['LandingPage']

        self.assertEqual(set(landing_page['properties']), {'header', 'hero', 'features', 'testimonials', 'cta'})

    def test_the_swagger_page_is_served_from_the_installed_package(self):
        page = self.client.get(reverse('swagger-ui'))

        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'drf_spectacular_sidecar')
        self.assertContains(page, reverse('schema'))

    def test_the_docs_stay_public_even_with_a_stale_token(self):
        response = self.client.get(reverse('schema'), HTTP_AUTHORIZATION='Bearer not-a-real-token')

        self.assertEqual(response.status_code, 200)


class ErrorResponsesTests(SimpleTestCase):
    def test_errors_sharing_a_status_code_become_one_response_with_an_example_each(self):
        responses = error_responses(VALIDATION_FAILED, DocumentedError.of(WeakPasswordError))

        self.assertEqual(list(responses), [400])
        self.assertEqual(len(responses[400].examples), 2)

    def test_an_exception_class_documents_itself(self):
        error = DocumentedError.of(EmailAlreadyRegisteredError)

        self.assertEqual(
            (error.status, error.code, error.message),
            (409, 'email_already_registered', 'An account with this email already exists.'),
        )
