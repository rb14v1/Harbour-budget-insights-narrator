"""Demo-data seed (data migration): a generated MonthlyInsight for each of
the most recent 2 months, so the seeded data demonstrates the full
narrator feature out of the box.

Calls the real compute_month_summary()/generate_budget_insights() - at
migrate time there is no OPENAI_API_KEY configured, so this exercises the
deterministic stub path exactly as the tests do.

Idempotent via update_or_create. Depends on transactions' 0002 migration,
which creates the transactions these aggregates are computed from.
"""
from datetime import date

from django.db import migrations


def _month_date(base_year: int, base_month: int, months_ago: int) -> date:
    year = base_year
    month = base_month - months_ago
    while month <= 0:
        month += 12
        year -= 1
    return date(year, month, 1)


def seed_insights(apps, schema_editor):
    # Real (non-historical) imports are used deliberately here so this
    # migration exercises the exact same aggregation/narration code paths
    # as the live API and the test suite, rather than duplicating them.
    from apps.accounts.models import User
    from apps.common.ai import generate_budget_insights
    from apps.insights.models import MonthlyInsight
    from apps.insights.services import compute_month_summary

    user = User.objects.filter(email="demo@example.com").first()
    if user is None:
        return

    today = date.today()
    for months_ago in (1, 0):
        month_date = _month_date(today.year, today.month, months_ago)
        summary = compute_month_summary(user, month_date)
        narrative = generate_budget_insights(
            month=month_date.strftime("%B %Y"),
            category_totals=summary["category_totals"],
            total_income=summary["total_income"],
            total_expenses=summary["total_expenses"],
            prior_month_category_totals=summary["prior_month_category_totals"],
        )
        MonthlyInsight.objects.update_or_create(
            user=user, month=month_date, defaults={"narrative": narrative},
        )


def unseed_insights(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    MonthlyInsight = apps.get_model("insights", "MonthlyInsight")

    user = User.objects.filter(email="demo@example.com").first()
    if user is not None:
        MonthlyInsight.objects.filter(user=user).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("insights", "0001_initial"),
        ("transactions", "0002_seed_demo_data"),
    ]

    operations = [
        migrations.RunPython(seed_insights, unseed_insights),
    ]
