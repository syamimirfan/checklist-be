from django.contrib import admin

from .models import LandingFeature, LandingPage, LandingTestimonial


@admin.register(LandingPage)
class LandingPageAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Header buttons', {'fields': ('header_login_label', 'header_signup_label')}),
        (
            'Hero',
            {
                'fields': (
                    'hero_badge',
                    'hero_title_prefix',
                    'hero_title_highlight',
                    'hero_title_suffix',
                    'hero_description',
                    'hero_cta_label',
                ),
            },
        ),
        ('Testimonials', {'fields': ('testimonials_title',)}),
        ('Closing call to action', {'fields': ('cta_title', 'cta_description', 'cta_button_label')}),
    )

    def has_add_permission(self, request):
        # The landing page is a single row: edit it instead of adding a second one.
        return not LandingPage.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


class LandingContentItemAdmin(admin.ModelAdmin):
    """Shared admin behaviour for the repeatable blocks: reorder and publish straight from the list."""

    list_editable = ('position', 'is_published')
    list_filter = ('is_published',)


@admin.register(LandingFeature)
class LandingFeatureAdmin(LandingContentItemAdmin):
    list_display = ('title', 'tone', 'position', 'is_published')
    search_fields = ('title', 'description')


@admin.register(LandingTestimonial)
class LandingTestimonialAdmin(LandingContentItemAdmin):
    list_display = ('author', 'role', 'position', 'is_published')
    search_fields = ('author', 'role', 'quote')
