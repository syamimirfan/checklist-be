from drf_spectacular.utils import extend_schema
from rest_framework.response import Response

from apps.core.views import PublicAPIView

from .serializers import LandingPageSerializer
from .services import LandingPageService


class LandingPageView(PublicAPIView):
    """GET /api/landing/ — all the content of the public landing page."""

    service = LandingPageService()

    @extend_schema(
        summary='Get the landing page content',
        description=(
            'Everything the landing page shows: header buttons, hero, features, testimonials and the closing '
            'call to action. Unpublished features and testimonials are left out.'
        ),
        responses=LandingPageSerializer,
    )
    def get(self, request):
        return Response(LandingPageSerializer(self.service.get_content()).data)
