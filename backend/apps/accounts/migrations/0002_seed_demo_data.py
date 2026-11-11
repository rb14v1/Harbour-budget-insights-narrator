"""Demo-data seed (data migration): one demo user so the rest of the
demo-data chain (categories -> transactions -> insights) has someone to
belong to.

Idempotent via get_or_create. Demo login: demo@example.com / demo12345
"""
from django.db import migrations


def seed_demo_user(apps, schema_editor):
    from django.contrib.auth.hashers import make_password

    User = apps.get_model("accounts", "User")
    user, created = User.objects.get_or_create(
        email="demo@example.com",
        defaults={"full_name": "Demo User", "is_active": True},
    )
    if created:
        # Historical model manager doesn't reliably carry the custom
        # create_user/set_password helpers, so hash the password directly
        # with the same hasher Django uses by default.
        user.password = make_password("demo12345")
        user.save()


def unseed_demo_user(apps, schema_editor):
    """Reverse migration: remove exactly the demo user (and, via cascade,
    everything seeded for them downstream). Safe no-op if already removed."""
    User = apps.get_model("accounts", "User")
    User.objects.filter(email="demo@example.com").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_demo_user, unseed_demo_user),
    ]
