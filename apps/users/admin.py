from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm

from .models import User


class UserCreationForm(AdminUserCreationForm):
    class Meta(AdminUserCreationForm.Meta):
        model = User
        fields = ('email', 'name')
        field_classes = {}


class UserEditForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        field_classes = {}


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = UserCreationForm
    form = UserEditForm

    list_display = ('email', 'name', 'email_verified', 'is_active', 'is_staff', 'created_at')
    list_filter = ('email_verified', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('email', 'name')
    ordering = ('-created_at',)
    readonly_fields = ('id', 'last_login', 'created_at', 'updated_at')

    fieldsets = (
        (None, {'fields': ('id', 'email', 'password')}),
        ('Profile', {'fields': ('name', 'email_verified')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('email', 'name', 'usable_password', 'password1', 'password2')}),
    )
