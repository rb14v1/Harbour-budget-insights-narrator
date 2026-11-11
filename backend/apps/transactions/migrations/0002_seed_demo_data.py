"""Demo-data seed (data migration): ~48 transactions spread across the
last 3 months (relative to whenever `migrate` runs) for the demo user, with
enough variation per category that month-over-month totals differ
meaningfully - this is what makes the generated narrative's percentage
comparisons non-trivial.

Idempotent via get_or_create, keyed on (user, category, transaction_date,
description), which is unique across every row in `ROWS` below. Depends on
categories' 0002 migration, which creates the categories these transactions
attach to.
"""
from datetime import date

from django.db import migrations

# (months_ago, category_name, transaction_type, amount, day_of_month, description)
ROWS = [
    # --- Two months ago ---
    (2, "Salary", "income", "3200.00", 1, "Monthly salary"),
    (2, "Groceries", "expense", "55.00", 3, "Weekly groceries"),
    (2, "Groceries", "expense", "48.00", 10, "Grocery run"),
    (2, "Groceries", "expense", "62.00", 18, "Supermarket"),
    (2, "Groceries", "expense", "40.00", 25, "Grocery restock"),
    (2, "Rent", "expense", "1200.00", 1, "Monthly rent"),
    (2, "Dining", "expense", "30.00", 5, "Dinner out"),
    (2, "Dining", "expense", "25.00", 12, "Takeout"),
    (2, "Dining", "expense", "35.00", 20, "Coffee shop"),
    (2, "Entertainment", "expense", "40.00", 8, "Movie night"),
    (2, "Entertainment", "expense", "20.00", 22, "Streaming subscription"),
    (2, "Transportation", "expense", "60.00", 2, "Gas"),
    (2, "Transportation", "expense", "55.00", 16, "Rideshare"),
    (2, "Utilities", "expense", "150.00", 6, "Electricity bill"),
    (2, "Utilities", "expense", "80.00", 19, "Water bill"),

    # --- Last month ---
    (1, "Salary", "income", "3200.00", 1, "Monthly salary"),
    (1, "Groceries", "expense", "60.00", 2, "Weekly groceries"),
    (1, "Groceries", "expense", "50.00", 9, "Grocery run"),
    (1, "Groceries", "expense", "70.00", 17, "Supermarket"),
    (1, "Groceries", "expense", "45.00", 24, "Grocery restock"),
    (1, "Groceries", "expense", "38.00", 28, "Costco run"),
    (1, "Rent", "expense", "1200.00", 1, "Monthly rent"),
    (1, "Dining", "expense", "40.00", 4, "Dinner out"),
    (1, "Dining", "expense", "55.00", 11, "Restaurant"),
    (1, "Dining", "expense", "60.00", 19, "Takeout"),
    (1, "Dining", "expense", "48.00", 26, "Brunch"),
    (1, "Entertainment", "expense", "35.00", 7, "Movie night"),
    (1, "Entertainment", "expense", "60.00", 21, "Concert tickets"),
    (1, "Transportation", "expense", "58.00", 3, "Gas"),
    (1, "Transportation", "expense", "62.00", 15, "Train pass"),
    (1, "Utilities", "expense", "140.00", 6, "Electricity bill"),
    (1, "Utilities", "expense", "95.00", 20, "Internet bill"),

    # --- This month ---
    (0, "Salary", "income", "3250.00", 1, "Monthly salary"),
    (0, "Groceries", "expense", "65.00", 2, "Weekly groceries"),
    (0, "Groceries", "expense", "58.00", 9, "Grocery run"),
    (0, "Groceries", "expense", "72.00", 16, "Supermarket"),
    (0, "Groceries", "expense", "50.00", 23, "Grocery restock"),
    (0, "Rent", "expense", "1200.00", 1, "Monthly rent"),
    (0, "Dining", "expense", "80.00", 5, "Dinner out"),
    (0, "Dining", "expense", "95.00", 13, "Restaurant"),
    (0, "Dining", "expense", "110.00", 21, "Takeout"),
    (0, "Dining", "expense", "60.00", 27, "Brunch"),
    (0, "Entertainment", "expense", "45.00", 8, "Movie night"),
    (0, "Entertainment", "expense", "30.00", 18, "Streaming subscription"),
    (0, "Transportation", "expense", "60.00", 4, "Gas"),
    (0, "Transportation", "expense", "65.00", 17, "Rideshare"),
    (0, "Utilities", "expense", "160.00", 7, "Electricity bill"),
    (0, "Utilities", "expense", "100.00", 22, "Water bill"),
]


def _month_date(base_year: int, base_month: int, months_ago: int, day: int = 1) -> date:
    year = base_year
    month = base_month - months_ago
    while month <= 0:
        month += 12
        year -= 1
    return date(year, month, min(day, 28))


def seed_transactions(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    Category = apps.get_model("categories", "Category")
    Transaction = apps.get_model("transactions", "Transaction")

    user = User.objects.filter(email="demo@example.com").first()
    if user is None:
        return

    categories = {c.name: c for c in Category.objects.filter(user=user)}
    today = date.today()

    for months_ago, category_name, txn_type, amount, day, description in ROWS:
        category = categories.get(category_name)
        if category is None:
            continue
        txn_date = _month_date(today.year, today.month, months_ago, day)
        Transaction.objects.get_or_create(
            user=user,
            category=category,
            transaction_date=txn_date,
            description=description,
            defaults={"transaction_type": txn_type, "amount": amount},
        )


def unseed_transactions(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    Transaction = apps.get_model("transactions", "Transaction")

    user = User.objects.filter(email="demo@example.com").first()
    if user is not None:
        Transaction.objects.filter(user=user).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("transactions", "0001_initial"),
        ("categories", "0002_seed_demo_data"),
    ]

    operations = [
        migrations.RunPython(seed_transactions, unseed_transactions),
    ]
