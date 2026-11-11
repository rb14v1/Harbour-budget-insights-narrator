from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.categories.models import Category
from apps.common.test_utils import auth_client, create_user
from apps.insights.models import MonthlyInsight
from apps.transactions.models import Transaction


class InsightMonthViewTests(APITestCase):
    def setUp(self):
        self.user = create_user(email="insights@example.com")
        self.client_a = auth_client(self.user)
        self.category = Category.objects.create(user=self.user, name="Dining")
        Transaction.objects.create(
            user=self.user, category=self.category, transaction_type="expense",
            amount="100.00", transaction_date="2026-11-05",
        )

    def test_fetch_returns_200_with_null_narrative_before_generation(self):
        response = self.client_a.get(reverse("insight-month", args=[2026, 11]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["narrative"])
        self.assertEqual(response.data["category_totals"], {"Dining": 100.00})

    def test_fetch_includes_narrative_after_generation(self):
        self.client_a.post(reverse("insight-generate", args=[2026, 11]))
        response = self.client_a.get(reverse("insight-month", args=[2026, 11]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data["narrative"])

    def test_invalid_month_returns_400(self):
        response = self.client_a.get(reverse("insight-month", args=[2026, 13]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_month_with_no_transactions_still_returns_200(self):
        response = self.client_a.get(reverse("insight-month", args=[2020, 1]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_income"], 0.0)
        self.assertEqual(response.data["total_expenses"], 0.0)
        self.assertIsNone(response.data["narrative"])

    def test_requires_authentication(self):
        from rest_framework.test import APIClient
        response = APIClient().get(reverse("insight-month", args=[2026, 11]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class InsightGenerateViewTests(APITestCase):
    def setUp(self):
        self.user = create_user(email="gen@example.com")
        self.client_a = auth_client(self.user)
        self.category = Category.objects.create(user=self.user, name="Groceries")
        Transaction.objects.create(
            user=self.user, category=self.category, transaction_type="expense",
            amount="60.00", transaction_date="2026-11-05",
        )

    def test_generate_creates_monthly_insight(self):
        response = self.client_a.post(reverse("insight-generate", args=[2026, 11]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data["narrative"])
        self.assertEqual(MonthlyInsight.objects.filter(user=self.user, month="2026-11-01").count(), 1)

    def test_regenerate_replaces_not_duplicates(self):
        self.client_a.post(reverse("insight-generate", args=[2026, 11]))
        self.assertEqual(MonthlyInsight.objects.filter(user=self.user, month="2026-11-01").count(), 1)

        # Add another transaction so the recomputed narrative differs, then
        # regenerate - should still be exactly one row for this user+month.
        Transaction.objects.create(
            user=self.user, category=self.category, transaction_type="expense",
            amount="500.00", transaction_date="2026-11-20",
        )
        second_response = self.client_a.post(reverse("insight-generate", args=[2026, 11]))
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        self.assertEqual(MonthlyInsight.objects.filter(user=self.user, month="2026-11-01").count(), 1)

        insight = MonthlyInsight.objects.get(user=self.user, month="2026-11-01")
        self.assertIn("560.00", insight.narrative)

    def test_regenerate_with_identical_data_is_byte_identical(self):
        first = self.client_a.post(reverse("insight-generate", args=[2026, 11]))
        second = self.client_a.post(reverse("insight-generate", args=[2026, 11]))
        self.assertEqual(first.data["narrative"], second.data["narrative"])

    def test_invalid_month_returns_400(self):
        response = self.client_a.post(reverse("insight-generate", args=[2026, 0]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_generate_scoped_to_requesting_user(self):
        other = create_user(email="gen-other@example.com")
        other_client = auth_client(other)
        other_client.post(reverse("insight-generate", args=[2026, 11]))

        # The other user's generate call must not have touched this user's
        # (nonexistent) insight.
        self.assertFalse(MonthlyInsight.objects.filter(user=self.user, month="2026-11-01").exists())
        self.assertTrue(MonthlyInsight.objects.filter(user=other, month="2026-11-01").exists())
