from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse
from rest_framework.exceptions import ValidationError

from apps.core.exception_handler import handle_exception
from apps.core.exceptions import ApplicationError


class TeapotError(ApplicationError):
    status_code = HTTPStatus.IM_A_TEAPOT
    code = 'teapot'
    message = 'I am a teapot.'


class ExceptionHandlerTests(TestCase):
    def test_application_errors_use_their_own_status_code_and_message(self):
        response = handle_exception(TeapotError(), {})

        self.assertEqual(response.status_code, 418)
        self.assertEqual(response.data, {'error': {'code': 'teapot', 'message': 'I am a teapot.', 'fields': {}}})

    def test_the_message_and_fields_can_be_overridden_when_raised(self):
        error = TeapotError('Custom.', fields={'name': ['Bad.']})

        self.assertEqual(
            handle_exception(error, {}).data,
            {'error': {'code': 'teapot', 'message': 'Custom.', 'fields': {'name': ['Bad.']}}},
        )

    def test_validation_errors_list_the_messages_per_field(self):
        error = ValidationError({'email': ['Enter a valid email address.'], 'name': ['Required.']})

        response = handle_exception(error, {})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data['error'],
            {
                'code': 'validation_error',
                'message': 'Enter a valid email address.',
                'fields': {'email': ['Enter a valid email address.'], 'name': ['Required.']},
            },
        )

    def test_errors_that_are_not_about_a_field_go_under_non_field_errors(self):
        response = handle_exception(ValidationError('Something is off.'), {})

        self.assertEqual(response.data['error']['fields'], {'non_field_errors': ['Something is off.']})

    def test_unexpected_exceptions_are_left_for_django_to_report(self):
        self.assertIsNone(handle_exception(RuntimeError('boom'), {}))


class CorsTests(TestCase):
    url = '/api/landing/'

    def test_allows_the_frontend_origin(self):
        response = self.client.get(self.url, HTTP_ORIGIN='http://localhost:3000')

        self.assertEqual(response['Access-Control-Allow-Origin'], 'http://localhost:3000')

    def test_does_not_allow_other_origins(self):
        response = self.client.get(self.url, HTTP_ORIGIN='https://evil.example.com')

        self.assertNotIn('Access-Control-Allow-Origin', response)

    def test_answers_the_preflight_request_for_a_login(self):
        response = self.client.options(
            reverse('authentication:login'),
            HTTP_ORIGIN='http://localhost:3000',
            HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST',
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS='content-type,authorization',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Access-Control-Allow-Origin'], 'http://localhost:3000')
        self.assertIn('authorization', response['Access-Control-Allow-Headers'])
