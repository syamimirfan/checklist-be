"""Gives every API error the same JSON shape, so the frontend only has to read `error.message`:

    {"error": {"code": "invalid_credentials", "message": "Invalid email or password.", "fields": {}}}

`fields` is only filled for validation errors and maps a field name to its list of messages.
"""

from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from .exceptions import ApplicationError


def error_body(code, message, fields=None):
    return {'error': {'code': code, 'message': message, 'fields': fields or {}}}


def handle_exception(exc, context):
    if isinstance(exc, ApplicationError):
        return Response(error_body(exc.code, exc.message, exc.fields), status=exc.status_code)

    response = drf_exception_handler(exc, context)
    if response is None:  # not an API error: let Django report it as a server error
        return None

    if isinstance(exc, ValidationError):
        fields = _field_messages(response.data)
        first_message = next(iter(fields.values()))[0]
        response.data = error_body('validation_error', first_message, fields)
    else:
        response.data = error_body(exc.get_codes(), str(exc.detail))
    return response


def _field_messages(detail):
    """Flatten DRF's validation detail into {field: [message, ...]}."""
    if isinstance(detail, dict):
        return {field: [str(m) for m in _as_list(messages)] for field, messages in detail.items()}
    return {'non_field_errors': [str(m) for m in _as_list(detail)]}


def _as_list(value):
    return value if isinstance(value, list) else [value]
