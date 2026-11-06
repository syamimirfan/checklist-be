"""Building blocks for describing the API in the OpenAPI schema (Swagger UI at /api/v1/).

Errors are documented from the same exception classes the services raise, so the codes and messages
shown in Swagger cannot drift from the real ones.
"""

from dataclasses import dataclass, field
from http import HTTPStatus

from drf_spectacular.utils import OpenApiExample, OpenApiResponse
from rest_framework import serializers

from .exception_handler import error_body
from .exceptions import ApplicationError


class ErrorBodySerializer(serializers.Serializer):
    code = serializers.CharField(help_text='Stable identifier to branch on, for example `invalid_credentials`.')
    message = serializers.CharField(help_text='Text that is safe to show to the user.')
    fields = serializers.DictField(
        child=serializers.ListField(child=serializers.CharField()),
        help_text='Messages per field. Only filled for validation errors.',
    )


class ErrorResponseSerializer(serializers.Serializer):
    error = ErrorBodySerializer()


@dataclass(frozen=True)
class DocumentedError:
    """One error an endpoint can answer with, as shown in Swagger."""

    status: int
    code: str
    message: str
    fields: dict = field(default_factory=dict)

    @classmethod
    def of(cls, error: type[ApplicationError]):
        """Describe an `ApplicationError` subclass by its own status code, code and message."""
        return cls(int(error.status_code), error.code, error.message)

    def example(self):
        return OpenApiExample(
            self.code,
            value=error_body(self.code, self.message, self.fields),
            response_only=True,
        )


VALIDATION_FAILED = DocumentedError(
    HTTPStatus.BAD_REQUEST,
    'validation_error',
    'Enter a valid email address.',
    {'email': ['Enter a valid email address.']},
)
THROTTLED = DocumentedError(
    HTTPStatus.TOO_MANY_REQUESTS,
    'throttled',
    'Request was throttled. Expected available in 42 seconds.',
)


def error_responses(*errors: DocumentedError):
    """The `responses` entries for an endpoint's errors, one per status code.

    Errors that share a status code (a 400 for a bad body and for a weak password) become one
    response with an example for each.
    """
    by_status = {}
    for error in errors:
        by_status.setdefault(int(error.status), []).append(error)

    return {
        status: OpenApiResponse(
            response=ErrorResponseSerializer,
            description=' / '.join(error.code for error in group),
            examples=[error.example() for error in group],
        )
        for status, group in by_status.items()
    }
