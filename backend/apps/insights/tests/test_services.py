from datetime import date

from django.test import TestCase

from apps.categories.models import Category
from apps.common.test_utils import create_user
from apps.insights.services import compute_category_totals, compute_month_summary
from apps.transactions.models import Transaction


class ComputeCategoryTotalsTests(TestCase):
    """Hand-construct a small known set of transactions and assert the
    computed totals are exactly right - the most important correctness
    test in this app."""

    def setUp(self):
        self.user = create_user(email="agg@example.com")
        self.groceries = Category.objects.create(user=self.user, name="Groceries")
        self.rent = Category.objects.create(user=self.user, name="Rent")
        self.dining = Category.objects.create(user=self.user, name="Dining")
        self.salary = Category.objects.create(user=self.user, name="Salary")

        # November 2026: known expense amounts per category.
        Transaction.objects.create(user=self.user, category=self.groceries, transaction_type="expense", amount="60.00", transaction_date="2026-11-02")
        Transaction.objects.create(user=self.user, category=self.groceries, transaction_type="expense", amount="40.00", transaction_date="2026-11-16")
        Transaction.objects.create(user=self.user, category=self.rent, transaction_type="expense", amount="1200.00", transaction_date="2026-11-01")
        Transaction.objects.create(user=self.user, category=self.dining, transaction_type="expense", amount="75.50", transaction_date="2026-11-20")
        # Income should never appear in category_totals.
        Transaction.objects.create(user=self.user, category=self.salary, transaction_type="income", amount="3000.00", transaction_date="2026-11-01")

        # A different month's data must not leak into November's totals.
        Transaction.objects.create(user=self.user, category=self.groceries, transaction_type="expense", amount="999.00", transaction_date="2026-10-05")

        # A different user's data must never leak in either.
        other_user = create_user(email="agg-other@example.com")
        other_category = Category.objects.create(user=other_user, name="Groceries")
        Transaction.objects.create(user=other_user, category=other_category, transaction_type="expense", amount="500.00", transaction_date="2026-11-05")

    def test_category_totals_are_exact(self):
        totals = compute_category_totals(self.user, date(2026, 11, 1))
        self.assertEqual(totals, {
            "Dining": 75.50,
            "Groceries": 100.00,
            "Rent": 1200.00,
        })

    def test_category_with_no_expenses_is_absent(self):
        totals = compute_category_totals(self.user, date(2026, 11, 1))
        self.assertNotIn("Salary", totals)

    def test_empty_month_returns_empty_dict(self):
        totals = compute_category_totals(self.user, date(2025, 1, 1))
        self.assertEqual(totals, {})


class ComputeMonthSummaryTests(TestCase):
    def setUp(self):
        self.user = create_user(email="summary@example.com")
        self.groceries = Category.objects.create(user=self.user, name="Groceries")
        self.rent = Category.objects.create(user=self.user, name="Rent")
        self.salary = Category.objects.create(user=self.user, name="Salary")

        # October (prior month): Groceries 80.
        Transaction.objects.create(user=self.user, category=self.groceries, transaction_type="expense", amount="80.00", transaction_date="2026-10-10")
        Transaction.objects.create(user=self.user, category=self.salary, transaction_type="income", amount="2500.00", transaction_date="2026-10-01")

        # November (current month): Groceries 100 (+25% vs Oct), Rent 1200.
        Transaction.objects.create(user=self.user, category=self.groceries, transaction_type="expense", amount="100.00", transaction_date="2026-11-10")
        Transaction.objects.create(user=self.user, category=self.rent, transaction_type="expense", amount="1200.00", transaction_date="2026-11-01")
        Transaction.objects.create(user=self.user, category=self.salary, transaction_type="income", amount="3000.00", transaction_date="2026-11-01")

    def test_summary_totals_are_exact(self):
        summary = compute_month_summary(self.user, date(2026, 11, 1))
        self.assertEqual(summary["total_income"], 3000.00)
        self.assertEqual(summary["total_expenses"], 1300.00)
        self.assertEqual(summary["category_totals"], {"Groceries": 100.00, "Rent": 1200.00})

    def test_prior_month_category_totals_are_exact(self):
        summary = compute_month_summary(self.user, date(2026, 11, 1))
        self.assertEqual(summary["prior_month_category_totals"], {"Groceries": 80.00})

    def test_prior_month_rolls_over_year_boundary(self):
        # January's "prior month" must be December of the previous year.
        Transaction.objects.create(user=self.user, category=self.groceries, transaction_type="expense", amount="25.00", transaction_date="2025-12-15")
        summary = compute_month_summary(self.user, date(2026, 1, 1))
        self.assertEqual(summary["prior_month_category_totals"], {"Groceries": 25.00})

    def test_month_with_no_transactions_returns_zeros(self):
        summary = compute_month_summary(self.user, date(2024, 3, 1))
        self.assertEqual(summary["total_income"], 0.0)
        self.assertEqual(summary["total_expenses"], 0.0)
        self.assertEqual(summary["category_totals"], {})
        self.assertEqual(summary["prior_month_category_totals"], {})
