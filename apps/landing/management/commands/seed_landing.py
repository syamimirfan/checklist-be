from django.core.management.base import BaseCommand
from django.db import transaction

from apps.landing.models import LandingFeature, LandingPage, LandingTestimonial

from ._constants import FEATURES, TESTIMONIALS


class Command(BaseCommand):
    help = (
        'Fill the landing page with its starter copy, features and testimonials. '
        'Anything that already exists is left alone, so it is safe to run again.'
    )

    @transaction.atomic
    def handle(self, *args, **options):
        if not LandingPage.objects.exists():
            LandingPage.objects.create()
            self.stdout.write('Created the landing page copy.')

        self._seed(LandingFeature, FEATURES, 'features')
        self._seed(LandingTestimonial, TESTIMONIALS, 'testimonials')

    def _seed(self, model, rows, label):
        if model.objects.exists():
            self.stdout.write(f'Kept the existing {label}.')
            return
        for position, row in enumerate(rows):
            model.objects.create(position=position, **row)
        self.stdout.write(f'Created {len(rows)} {label}.')
