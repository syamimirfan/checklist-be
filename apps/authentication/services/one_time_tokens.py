from abc import ABC, abstractmethod

from django.db import transaction
from django.utils import timezone

from apps.authentication.opaque_tokens import generate_opaque_token, hash_opaque_token


class OneTimeTokenService(ABC):
    """Issues and redeems the single-use tokens that are emailed to a user.

    Email verification and password reset work the same way and differ only in which table holds
    the tokens, how long they live and which error a bad token raises. Subclasses supply those three
    things and add their own use cases on top of `issue` and `redeem`.
    """

    @property
    @abstractmethod
    def model(self):
        """The `OneTimeToken` subclass that stores this kind of token."""

    @property
    @abstractmethod
    def lifetime(self):
        """How long a new token stays valid, as a timedelta."""

    @property
    @abstractmethod
    def invalid_error(self):
        """The `ApplicationError` raised for an unknown, used or expired token."""

    def issue(self, user):
        """Create a token for `user`, replacing any unused one, and return its raw value."""
        token = generate_opaque_token()
        with transaction.atomic():
            self.model.objects.filter(user=user, used_at__isnull=True).delete()
            self.model.objects.create(
                user=user,
                token_hash=hash_opaque_token(token),
                expires_at=timezone.now() + self.lifetime,
            )
        return token

    def redeem(self, token):
        """Mark `token` as used and return its user, or raise `invalid_error` if it can't be used.

        Callers that do more work with the result should wrap both steps in `transaction.atomic()`,
        so a failure in the second step gives the token back.
        """
        with transaction.atomic():
            record = (
                self.model.objects.select_for_update(of=('self',))
                .select_related('user')
                .filter(token_hash=hash_opaque_token(token))
                .first()
            )
            if record is None or not record.is_usable or not record.user.is_active:
                raise self.invalid_error()
            record.mark_used()
        return record.user
