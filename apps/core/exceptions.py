from http import HTTPStatus


class ApplicationError(Exception):
    """An expected failure that is reported to the API client instead of crashing the request.

    Subclasses set `status_code`, `code` and a default `message`. Raise one from a service and
    `apps.core.exception_handler` turns it into the standard JSON error response.
    """

    status_code = HTTPStatus.BAD_REQUEST
    code = 'error'
    message = 'Something went wrong.'

    def __init__(self, message=None, *, fields=None):
        self.message = message or self.message
        self.fields = fields or {}
        super().__init__(self.message)
