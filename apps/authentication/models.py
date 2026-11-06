from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import UUIDModel


class UserSession(UUIDModel):
    """One signed-in device: the `sessions` table from the ERD.

    `refresh_token_hash` is stored in the ERD's `refresh_token` column, but holds only the digest
    of the token the client received.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sessions')
    refresh_token_hash = models.CharField(max_length=64, unique=True, db_column='refresh_token')
    user_agent = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sessions'

    def __str__(self):
        return f'{self.user_id} until {self.expires_at:%Y-%m-%d %H:%M}'

    @property
    def is_expired(self):
        return self.expires_at <= timezone.now()


class OneTimeToken(UUIDModel):
    """Abstract base for a token that is emailed to a user and can be redeemed once.

    Like sessions, only the digest of the emailed token is stored (in the ERD's `token` column).
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token_hash = models.CharField(max_length=64, unique=True, db_column='token')
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f'{self.user_id} until {self.expires_at:%Y-%m-%d %H:%M}'

    @property
    def is_usable(self):
        return self.used_at is None and self.expires_at > timezone.now()

    def mark_used(self):
        self.used_at = timezone.now()
        self.save(update_fields=['used_at'])


class EmailVerification(OneTimeToken):
    class Meta:
        db_table = 'email_verifications'


class PasswordReset(OneTimeToken):
    class Meta:
        db_table = 'password_resets'
