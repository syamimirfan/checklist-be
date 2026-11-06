from django.contrib import admin

from .models import EmailVerification, PasswordReset, UserSession


class ReadOnlyAdmin(admin.ModelAdmin):
    """These rows are created by the sign-in and email flows, so the admin only lets staff look at them.

    Deleting is still allowed: removing a session signs that device out.
    """

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(UserSession)
class UserSessionAdmin(ReadOnlyAdmin):
    list_display = ('user', 'ip_address', 'user_agent', 'created_at', 'expires_at')
    search_fields = ('user__email', 'ip_address')
    ordering = ('-created_at',)
    exclude = ('refresh_token_hash',)


class OneTimeTokenAdmin(ReadOnlyAdmin):
    """Shared admin for the emailed-token tables. The token digest is never shown."""

    list_display = ('user', 'expires_at', 'used_at')
    search_fields = ('user__email',)
    ordering = ('-expires_at',)
    exclude = ('token_hash',)


@admin.register(EmailVerification)
class EmailVerificationAdmin(OneTimeTokenAdmin):
    pass


@admin.register(PasswordReset)
class PasswordResetAdmin(OneTimeTokenAdmin):
    pass
