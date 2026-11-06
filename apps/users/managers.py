from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    """Manager for a user model that logs in with an email address instead of a username."""

    use_in_migrations = True

    def get_by_natural_key(self, email):
        return super().get_by_natural_key(email.strip().lower())

    def _create_user(self, email, name, password, **extra_fields):
        if not email:
            raise ValueError('The email address must be set.')
        user = self.model(email=self.normalize_email(email), name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, name, password, **extra_fields)

    def create_superuser(self, email, name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('email_verified', True)

        if extra_fields['is_staff'] is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields['is_superuser'] is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self._create_user(email, name, password, **extra_fields)
