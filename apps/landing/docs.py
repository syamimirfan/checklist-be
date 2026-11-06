"""What Swagger shows for the landing endpoint. The view applies it as a decorator: `@docs.landing_page`.

The errors come from the table in `error_messages.py`, the same one the view uses for its real error
responses, so the codes and messages in Swagger cannot drift from the real ones.
"""

from drf_spectacular.utils import extend_schema

from apps.core.api_docs import DocumentedError, error_responses

from .error_messages import ERROR_COPY
from .serializers import LandingPageSerializer

LANDING_ERRORS = tuple(
    DocumentedError(status, copy.code, copy.message) for status, copy in ERROR_COPY.items()
)

landing_page = extend_schema(
    summary='Get the landing page content',
    description=(
        'Landing page content is public and read-only. It is used by the frontend to render the landing page, '
    ),
    responses={200: LandingPageSerializer, **error_responses(*LANDING_ERRORS)},
)
