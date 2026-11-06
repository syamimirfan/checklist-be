from rest_framework.permissions import AllowAny
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView


class PublicAPIView(APIView):
    """Base for endpoints that anyone can call, signed in or not.

    Set `throttle_scope` on a subclass to rate-limit it; the rate for that scope lives in
    `REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']`. Without a scope the view is not throttled.
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
