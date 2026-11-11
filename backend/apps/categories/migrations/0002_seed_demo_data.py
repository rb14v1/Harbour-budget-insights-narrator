"""Demo-data seed (data migration): standard categories for the demo user.

Idempotent via get_or_create. Depends on accounts' 0002 migration, which
creates the demo user this seed attaches categories to.
"""
from django.db import migrations

CATEGORY_NAMES = [
    "Salary",
    "Groceries",
    "Rent",
    "Dining",
    "Entertainment",
    "Transportation",
    "Utilities",
]


def seed_categories(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    Category = apps.get_model("categories", "Category")

    user = User.objects.filter(email="demo@example.com").first()
    if user is None:
        return

    for name in CATEGORY_NAMES:
        Category.objects.get_or_create(user=user, name=name)


def unseed_categories(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    Category = apps.get_model("categories", "Category")

    user = User.objects.filter(email="demo@example.com").first()
    if user is not None:
        Category.objects.filter(user=user, name__in=CATEGORY_NAMES).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("categories", "0001_initial"),
        ("accounts", "0002_seed_demo_data"),
    ]

    operations = [
        migrations.RunPython(seed_categories, unseed_categories),
    ]
