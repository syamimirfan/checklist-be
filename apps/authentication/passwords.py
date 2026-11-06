from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .exceptions import WeakPasswordError


def validate_new_password(password, user, *, field='password'):
    """Check `password` against the validators in `AUTH_PASSWORD_VALIDATORS`.

    `user` (saved or not) lets the similarity validator compare it with the user's name and email.
    Raises `WeakPasswordError`, with the messages filed under `field`, if it is not acceptable.
    """
    try:
        validate_password(password, user)
    except ValidationError as error:
        raise WeakPasswordError(error.messages[0], fields={field: error.messages}) from error
