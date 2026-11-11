from django.test import TestCase, override_settings

from apps.common.ai import generate_budget_insights, is_stub_mode


@override_settings(OPENAI_API_KEY="")
class StubNarrativeDeterminismTests(TestCase):
    def test_stub_mode_is_active_without_api_key(self):
        self.assertTrue(is_stub_mode())

    def test_same_inputs_produce_byte_identical_output(self):
        kwargs = dict(
            month="November 2026",
            category_totals={"Rent": 1200.0, "Dining": 420.0, "Groceries": 300.0},
            total_income=3000.0,
            total_expenses=1920.0,
            prior_month_category_totals={"Rent": 1200.0, "Dining": 340.0, "Groceries": 310.0},
        )
        first = generate_budget_insights(**kwargs)
        second = generate_budget_insights(**kwargs)
        self.assertEqual(first, second)

    def test_output_independent_of_dict_key_order(self):
        kwargs_a = dict(
            month="November 2026",
            category_totals={"Rent": 1200.0, "Dining": 420.0},
            total_income=3000.0,
            total_expenses=1620.0,
            prior_month_category_totals=None,
        )
        kwargs_b = dict(
            month="November 2026",
            category_totals={"Dining": 420.0, "Rent": 1200.0},
            total_income=3000.0,
            total_expenses=1620.0,
            prior_month_category_totals=None,
        )
        self.assertEqual(generate_budget_insights(**kwargs_a), generate_budget_insights(**kwargs_b))

    def test_mentions_top_category_and_amount(self):
        narrative = generate_budget_insights(
            month="November 2026",
            category_totals={"Rent": 1200.0, "Dining": 420.0},
            total_income=3000.0,
            total_expenses=1620.0,
            prior_month_category_totals=None,
        )
        self.assertIn("Rent", narrative)
        self.assertIn("1,200.00", narrative)

    def test_percent_change_vs_prior_month(self):
        narrative = generate_budget_insights(
            month="November 2026",
            category_totals={"Dining": 420.0},
            total_income=1000.0,
            total_expenses=420.0,
            prior_month_category_totals={"Dining": 350.0},
        )
        # (420 - 350) / 350 = 20% increase
        self.assertIn("20% more than last month", narrative)

    def test_no_expenses_produces_distinct_sentence(self):
        narrative = generate_budget_insights(
            month="November 2026",
            category_totals={},
            total_income=1000.0,
            total_expenses=0.0,
            prior_month_category_totals=None,
        )
        self.assertIn("no expenses", narrative)

    def test_shortfall_is_mentioned_when_expenses_exceed_income(self):
        narrative = generate_budget_insights(
            month="November 2026",
            category_totals={"Rent": 2000.0},
            total_income=1000.0,
            total_expenses=2000.0,
            prior_month_category_totals=None,
        )
        self.assertIn("shortfall", narrative)


@override_settings(OPENAI_API_KEY="sk-fake-key-for-test")
class RealModeDetectionTests(TestCase):
    def test_stub_mode_is_inactive_when_key_set(self):
        self.assertFalse(is_stub_mode())
