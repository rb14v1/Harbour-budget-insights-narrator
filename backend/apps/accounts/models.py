from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.accounts.managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """Single-role user. Every app scopes its queryset to request.user -
    there is no admin/manager distinction in this demo app beyond Django's
    own is_staff/is_superuser for the admin site.

    No `username` field; `full_name` is a single free-text field rather
    than Django's default first_name/last_name split, since this app has
    no need to address users formally in separate parts."""

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=150, blank=True, default="")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email
