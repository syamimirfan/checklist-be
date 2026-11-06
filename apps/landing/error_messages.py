"""The message for each HTTP error status of `GET /api/landing/`, in the error body
(`{"error": {"code": ..., "message": ...}}`). The 200 response does not carry them.

Three of them are raised by this endpoint itself. It is public and read-only, so it has no sign-in,
no input to reject and no rate limit:

- 405: any method other than GET, HEAD or OPTIONS.
- 406: an `Accept` header the JSON response cannot satisfy.
- 500: something unexpected on our side, such as the database being unreachable.

The other three (401, 403, 404) are documented so the frontend knows their wording, but this endpoint
does not raise them today: there is no sign-in or permission to check, and its URL always exists.

These are plain constants, not database rows: change the wording here and deploy. The view puts these
messages into its real error responses and Swagger documents the same codes and messages, so the two
cannot drift apart.

`code` is the stable identifier in the standard error body (`{"error": {"code": ...}}`). Where DRF
raises the same error (401, 403, 404, 405, 406) it is DRF's own code, so the docs match real responses.
"""

from typing import NamedTuple


class ErrorCopy(NamedTuple):
    code: str
    message: str


ERROR_COPY = {
    401: ErrorCopy('not_authenticated', 'You need to sign in to continue.'),
    403: ErrorCopy('permission_denied', "You don't have permission to do that."),
    404: ErrorCopy('not_found', "We couldn't find what you were looking for."),
    405: ErrorCopy('method_not_allowed', "That action isn't supported here."),
    406: ErrorCopy('not_acceptable', "We can't send the response in the format your app asked for."),
    500: ErrorCopy('server_error', 'Something went wrong on our side. Please try again later.'),
}

ERROR_MESSAGES = {status: copy.message for status, copy in ERROR_COPY.items()}
