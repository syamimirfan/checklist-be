from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.landing.models import LandingFeature, LandingPage, LandingTestimonial

User = get_user_model()


class LandingAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser('root@example.com', 'Root', 'a-strong-pass-1')

    def setUp(self):
        self.client.force_login(self.admin)

    def test_the_landing_page_can_be_created_once(self):
        add_url = reverse('admin:landing_landingpage_add')
        self.assertEqual(self.client.get(add_url).status_code, 200)

        LandingPage.objects.create()

        self.assertEqual(self.client.get(add_url).status_code, 403)

    def test_the_landing_page_can_be_edited_but_not_deleted(self):
        page = LandingPage.objects.create()

        response = self.client.post(
            reverse('admin:landing_landingpage_change', args=[page.pk]),
            {
                'header_login_label': 'Sign in',
                'header_signup_label': page.header_signup_label,
                'hero_badge': page.hero_badge,
                'hero_title_prefix': page.hero_title_prefix,
                'hero_title_highlight': page.hero_title_highlight,
                'hero_title_suffix': page.hero_title_suffix,
                'hero_description': page.hero_description,
                'hero_cta_label': page.hero_cta_label,
                'testimonials_title': page.testimonials_title,
                'cta_title': page.cta_title,
                'cta_description': page.cta_description,
                'cta_button_label': page.cta_button_label,
            },
        )

        self.assertEqual(response.status_code, 302)
        page.refresh_from_db()
        self.assertEqual(page.header_login_label, 'Sign in')
        delete_url = reverse('admin:landing_landingpage_delete', args=[page.pk])
        self.assertEqual(self.client.get(delete_url).status_code, 403)

    def test_features_and_testimonials_are_listed(self):
        LandingFeature.objects.create(title='Shared workspaces', description='d')
        LandingTestimonial.objects.create(quote='q', author='Priya Nair', role='Lead')

        features = self.client.get(reverse('admin:landing_landingfeature_changelist'))
        testimonials = self.client.get(reverse('admin:landing_landingtestimonial_changelist'))

        self.assertContains(features, 'Shared workspaces')
        self.assertContains(testimonials, 'Priya Nair')
