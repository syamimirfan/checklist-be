from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.landing.models import LandingFeature, LandingPage, LandingTestimonial, Tone

LANDING = 'landing:landing-page'


def seed_landing():
    call_command('seed_landing', stdout=StringIO())


class LandingPageApiTests(TestCase):
    def fetch(self):
        response = self.client.get(reverse(LANDING))
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_is_public(self):
        self.assertEqual(self.client.get(reverse(LANDING)).status_code, 200)

    def test_serves_the_default_copy_before_anything_is_saved(self):
        body = self.fetch()

        self.assertEqual(
            body['header'],
            {'login_label': 'Log in', 'signup_label': 'Sign up free'},
        )
        self.assertEqual(
            body['hero'],
            {
                'badge': 'Now with shared workspaces',
                'title_prefix': 'Checklists that keep your',
                'title_highlight': 'whole team',
                'title_suffix': 'in sync',
                'description': 'Plan launches, track recurring work, and never lose a task in a chat thread again.',
                'cta_label': 'Read the Documentation',
            },
        )
        self.assertEqual(body['testimonials'], {'title': 'Trusted by teams who ship', 'items': []})
        self.assertEqual(
            body['cta'],
            {
                'title': 'Ready to get organized?',
                'description': 'Create a free account — no credit card required.',
                'button_label': 'Create your workspace',
            },
        )
        self.assertEqual(body['features'], [])
        self.assertFalse(LandingPage.objects.exists())  # reading the page never writes

    def test_serves_features_and_testimonials_in_position_order(self):
        LandingFeature.objects.create(title='Second', description='b', tone=Tone.PINK, position=2)
        LandingFeature.objects.create(title='First', description='a', tone=Tone.VIOLET, position=1)
        LandingTestimonial.objects.create(quote='Two', author='B', role='Role B', position=2)
        LandingTestimonial.objects.create(quote='One', author='A', role='Role A', position=1)

        body = self.fetch()

        self.assertEqual([f['title'] for f in body['features']], ['First', 'Second'])
        self.assertEqual(
            set(body['features'][0]),
            {'id', 'title', 'description', 'tone'},
        )
        self.assertEqual(body['features'][0]['tone'], 'violet')
        self.assertEqual([t['author'] for t in body['testimonials']['items']], ['A', 'B'])
        self.assertEqual(
            set(body['testimonials']['items'][0]),
            {'id', 'quote', 'author', 'role'},
        )

    def test_hides_unpublished_items(self):
        LandingFeature.objects.create(title='Live', description='a')
        LandingFeature.objects.create(title='Draft', description='b', is_published=False)
        LandingTestimonial.objects.create(quote='q', author='Live', role='r')
        LandingTestimonial.objects.create(quote='q', author='Draft', role='r', is_published=False)

        body = self.fetch()

        self.assertEqual([f['title'] for f in body['features']], ['Live'])
        self.assertEqual([t['author'] for t in body['testimonials']['items']], ['Live'])

    def test_serves_edited_copy(self):
        LandingPage.objects.create(
            hero_badge='New badge',
            testimonials_title='Loved by teams',
            cta_button_label='Get started',
            header_login_label='Sign in',
        )

        body = self.fetch()

        self.assertEqual(body['hero']['badge'], 'New badge')
        self.assertEqual(body['testimonials']['title'], 'Loved by teams')
        self.assertEqual(body['cta']['button_label'], 'Get started')
        self.assertEqual(body['header']['login_label'], 'Sign in')
        self.assertEqual(body['header']['signup_label'], 'Sign up free')  # untouched fields keep their default

    def test_only_allows_get(self):
        response = self.client.post(reverse(LANDING))

        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json()['error']['code'], 'method_not_allowed')

    def test_a_visitor_with_a_bad_token_still_gets_the_page(self):
        response = self.client.get(reverse(LANDING), HTTP_AUTHORIZATION='Bearer not-a-jwt')

        self.assertEqual(response.status_code, 200)


class SeedLandingTests(TestCase):
    def test_loads_the_content_the_frontend_used_to_hard_code(self):
        seed_landing()

        body = self.client.get(reverse(LANDING)).json()

        self.assertEqual(
            [(f['title'], f['tone']) for f in body['features']],
            [
                ('Shared workspaces', 'violet'),
                ('Templates that stick', 'fuchsia'),
                ('Tags & due dates', 'pink'),
                ('Comments built in', 'purple'),
            ],
        )
        self.assertEqual(
            [t['author'] for t in body['testimonials']['items']],
            ['Priya Nair', 'Marcus Webb', 'Elena Ruiz'],
        )

    def test_can_be_run_again_without_duplicating_or_overwriting(self):
        seed_landing()
        LandingFeature.objects.filter(title='Shared workspaces').update(title='Edited in the admin')
        LandingPage.objects.update(hero_badge='Edited badge')

        seed_landing()

        self.assertEqual(LandingFeature.objects.count(), 4)
        self.assertEqual(LandingTestimonial.objects.count(), 3)
        self.assertEqual(LandingPage.objects.count(), 1)
        self.assertTrue(LandingFeature.objects.filter(title='Edited in the admin').exists())
        self.assertEqual(LandingPage.objects.get().hero_badge, 'Edited badge')


class LandingModelTests(TestCase):
    def test_features_and_testimonials_share_the_ordering_and_publishing_base(self):
        for model in (LandingFeature, LandingTestimonial):
            with self.subTest(model=model.__name__):
                self.assertEqual(model._meta.ordering, ['position', 'created_at'])
                self.assertTrue(hasattr(model.objects, 'published'))

    def test_every_tone_is_one_the_frontend_can_render(self):
        self.assertEqual(
            set(Tone.values),
            {'violet', 'purple', 'fuchsia', 'pink', 'rose'},
        )
