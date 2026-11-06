from django.db import models

from apps.core.models import UUIDModel


class Tone(models.TextChoices):
    """Brand colours the frontend knows how to render (its `ToneName` type)."""

    VIOLET = 'violet', 'Violet'
    PURPLE = 'purple', 'Purple'
    FUCHSIA = 'fuchsia', 'Fuchsia'
    PINK = 'pink', 'Pink'
    ROSE = 'rose', 'Rose'


class LandingPage(UUIDModel):
    """The fixed copy on the public landing page: header buttons, hero and the closing call to action.

    Meant to hold a single row, edited in the admin. Every field defaults to the text the page
    shipped with, so the page renders correctly even before a row exists (see `load`).
    """

    header_login_label = models.CharField(max_length=40, default='Log in')
    header_signup_label = models.CharField(max_length=40, default='Sign up free')

    hero_badge = models.CharField(max_length=80, default='Now with shared workspaces')
    hero_title_prefix = models.CharField(max_length=120, default='Checklists that keep your')
    hero_title_highlight = models.CharField(
        max_length=60,
        default='whole team',
        help_text='Shown in the brand gradient, between the prefix and the suffix.',
    )
    hero_title_suffix = models.CharField(max_length=120, default='in sync')
    hero_description = models.TextField(
        default='Plan launches, track recurring work, and never lose a task in a chat thread again.',
    )
    hero_cta_label = models.CharField(max_length=60, default='Read the Documentation')

    testimonials_title = models.CharField(max_length=120, default='Trusted by teams who ship')

    cta_title = models.CharField(max_length=120, default='Ready to get organized?')
    cta_description = models.CharField(
        max_length=200,
        default='Create a free account — no credit card required.',
    )
    cta_button_label = models.CharField(max_length=60, default='Create your workspace')

    class Meta:
        db_table = 'landing_page'

    def __str__(self):
        return 'Landing page'

    @classmethod
    def load(cls):
        """The page's copy: the saved row, or an unsaved one holding the defaults if none exists yet."""
        return cls.objects.first() or cls()


class LandingContentQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_published=True)


class LandingContentItem(UUIDModel):
    """Abstract base for the repeatable blocks of the landing page (features, testimonials).

    Items are shown in `position` order, and only while `is_published` is on.
    """

    position = models.PositiveSmallIntegerField(default=0, help_text='Lower numbers appear first.')
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = LandingContentQuerySet.as_manager()

    class Meta:
        abstract = True
        ordering = ['position', 'created_at']


class LandingFeature(LandingContentItem):
    title = models.CharField(max_length=100)
    description = models.TextField()
    tone = models.CharField(max_length=20, choices=Tone.choices, default=Tone.VIOLET)

    class Meta(LandingContentItem.Meta):
        db_table = 'landing_features'

    def __str__(self):
        return self.title


class LandingTestimonial(LandingContentItem):
    quote = models.TextField()
    author = models.CharField(max_length=100)
    role = models.CharField(max_length=150)

    class Meta(LandingContentItem.Meta):
        db_table = 'landing_testimonials'

    def __str__(self):
        return f'{self.author} ({self.role})'
