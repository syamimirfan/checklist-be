from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.core.models import UUIDModel

from .managers import UserManager


class User(UUIDModel, AbstractBaseUser, PermissionsMixin):
    """The `users` table from the ERD. Logs in with `email`; the password hash is stored in `password_hash`."""

    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    password = models.CharField('password', max_length=128, db_column='password_hash')
    email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Not in the ERD, but required by Django's admin and permission system.
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

    def change_password(self, raw_password):
        """Store a new password hash. Strength is checked by the caller, not here."""
        self.set_password(raw_password)
        self.save(update_fields=['password', 'updated_at'])

    def mark_email_verified(self):
        self.email_verified = True
        self.save(update_fields=['email_verified', 'updated_at'])

    def record_login(self):
        self.last_login = timezone.now()
        self.save(update_fields=['last_login'])
