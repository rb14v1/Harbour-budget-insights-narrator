"""Pure Postgres/Django aggregation - no AI here. These functions compute
structured numbers from real Transaction rows; apps/common/ai.py turns
those numbers into a narrative. Keeping this layer separate means the AI
never sees individual raw transactions, only aggregates."""
from datetime import date
from decimal import Decimal

from django.db.models import Sum

from apps.transactions.models import Transaction


def _previous_month(month: date) -> date:
    if month.month == 1:
        return date(month.year - 1, 12, 1)
    return date(month.year, month.month - 1, 1)


def compute_category_totals(user, month: date) -> dict:
    """Total EXPENSE amount per category name for `month` (first-of-month
    date). Only expense transactions are included - this is a spending
    breakdown, not an income breakdown. Categories with no expenses that
    month are simply absent from the dict."""
    rows = (
        Transaction.objects.filter(
            user=user,
            transaction_type=Transaction.Type.EXPENSE,
            transaction_date__year=month.year,
            transaction_date__month=month.month,
        )
        .values("category__name")
        .annotate(total=Sum("amount"))
        .order_by("category__name")
    )
    return {row["category__name"]: float(row["total"]) for row in rows}


def compute_month_summary(user, month: date) -> dict:
    """Aggregate everything apps/common/ai.py needs to narrate `month`:
    total_income, total_expenses, category_totals (this month's expense
    breakdown) and prior_month_category_totals (same, for the month
    before)."""
    category_totals = compute_category_totals(user, month)
    prior_month_category_totals = compute_category_totals(user, _previous_month(month))

    income_total = Transaction.objects.filter(
        user=user,
        transaction_type=Transaction.Type.INCOME,
        transaction_date__year=month.year,
        transaction_date__month=month.month,
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

    expense_total = sum(category_totals.values()) if category_totals else 0.0

    return {
        "total_income": float(income_total),
        "total_expenses": float(expense_total),
        "category_totals": category_totals,
        "prior_month_category_totals": prior_month_category_totals,
    }
