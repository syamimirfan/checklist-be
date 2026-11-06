import uuid

from django.db import models


class UUIDModel(models.Model):
    """Abstract base for models whose primary key is a UUID (every table in the ERD)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True
