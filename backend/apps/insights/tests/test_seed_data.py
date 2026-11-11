from datetime import date

from django.test import TestCase

from apps.accounts.models import User
from apps.categories.models import Category
from apps.insights.models import MonthlyInsight
from apps.transactions.models import Transaction


class SeedDataTests(TestCase):
    """Assertions on the demo data created by the 0002_seed_demo_data data
    migrations (accounts -> categories -> transactions -> insights). These
    migrations run automatically for the Django test database, so this
    doubles as a regression test for the seed chain itself."""

    def setUp(self):
        self.user = User.objects.get(email="demo@example.com")

    def test_demo_user_exists(self):
        self.assertTrue(User.objects.filter(email="demo@example.com").exists())

    def test_demo_user_password_is_usable(self):
        self.assertTrue(self.user.check_password("demo12345"))

    def test_at_least_six_categories_seeded(self):
        count = Category.objects.filter(user=self.user).count()
        self.assertGreaterEqual(count, 6)

    def test_expected_category_names_present(self):
        names = set(Category.objects.filter(user=self.user).values_list("name", flat=True))
        for expected in ["Salary", "Groceries", "Rent", "Dining", "Entertainment", "Transportation", "Utilities"]:
            self.assertIn(expected, names)

    def test_forty_to_fifty_transactions_seeded(self):
        count = Transaction.objects.filter(user=self.user).count()
        self.assertGreaterEqual(count, 40)
        self.assertLessEqual(count, 60)

    def test_recent_months_have_generated_insights(self):
        today = date.today()
        this_month = date(today.year, today.month, 1)
        last_month_year = today.year if today.month > 1 else today.year - 1
        last_month_month = today.month - 1 if today.month > 1 else 12
        last_month = date(last_month_year, last_month_month, 1)

        self.assertTrue(MonthlyInsight.objects.filter(user=self.user, month=this_month).exists())
        self.assertTrue(MonthlyInsight.objects.filter(user=self.user, month=last_month).exists())

    def test_seeded_insight_narratives_are_non_empty(self):
        insights = MonthlyInsight.objects.filter(user=self.user)
        self.assertGreaterEqual(insights.count(), 2)
        for insight in insights:
            self.assertTrue(insight.narrative.strip())
