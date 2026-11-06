from dataclasses import dataclass

from django.db.models import QuerySet

from .models import LandingFeature, LandingPage, LandingTestimonial


@dataclass(frozen=True)
class LandingPageContent:
    """Everything the landing page shows, ready to be serialized."""

    page: LandingPage
    features: QuerySet[LandingFeature]
    testimonials: QuerySet[LandingTestimonial]


class LandingPageService:
    """Assembles the landing page content from its parts."""

    def get_content(self):
        return LandingPageContent(
            page=LandingPage.load(),
            features=LandingFeature.objects.published(),
            testimonials=LandingTestimonial.objects.published(),
        )
