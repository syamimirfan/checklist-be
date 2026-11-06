"""Shapes `LandingPageContent` into the JSON the landing page renders, one nested block per page section.

Each block reads its own prefixed fields off the single `LandingPage` row (`source='page'`).
"""

from rest_framework import serializers

from .models import LandingFeature, LandingTestimonial


class HeaderSerializer(serializers.Serializer):
    login_label = serializers.CharField(source='header_login_label')
    signup_label = serializers.CharField(source='header_signup_label')


class HeroSerializer(serializers.Serializer):
    badge = serializers.CharField(source='hero_badge')
    title_prefix = serializers.CharField(source='hero_title_prefix')
    title_highlight = serializers.CharField(source='hero_title_highlight')
    title_suffix = serializers.CharField(source='hero_title_suffix')
    description = serializers.CharField(source='hero_description')
    cta_label = serializers.CharField(source='hero_cta_label')


class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandingFeature
        fields = ('id', 'title', 'description', 'tone')


class TestimonialSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandingTestimonial
        fields = ('id', 'quote', 'author', 'role')


class TestimonialsSerializer(serializers.Serializer):
    title = serializers.CharField(source='page.testimonials_title')
    items = TestimonialSerializer(source='testimonials', many=True)


class CallToActionSerializer(serializers.Serializer):
    title = serializers.CharField(source='cta_title')
    description = serializers.CharField(source='cta_description')
    button_label = serializers.CharField(source='cta_button_label')


class LandingPageSerializer(serializers.Serializer):
    header = HeaderSerializer(source='page')
    hero = HeroSerializer(source='page')
    features = FeatureSerializer(many=True)
    testimonials = TestimonialsSerializer(source='*')
    cta = CallToActionSerializer(source='page')
