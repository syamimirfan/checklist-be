from rest_framework.response import Response

from apps.core.views import PublicAPIView

from . import docs
from .error_messages import ERROR_MESSAGES
from .serializers import LandingPageSerializer
from .services import LandingPageService


class LandingPageView(PublicAPIView):
    """GET /api/landing/ — all the content of the public landing page."""

    service = LandingPageService()

    @docs.landing_page
    def get(self, request):
        return Response(LandingPageSerializer(self.service.get_content()).data)

    def handle_exception(self, exc):
        """Word the error the way the landing page documents it (see `error_messages.py`)."""
        response = super().handle_exception(exc)
        message = ERROR_MESSAGES.get(response.status_code)
        if message:
            response.data['error']['message'] = message
        return response
