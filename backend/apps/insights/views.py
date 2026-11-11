from datetime import date

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.ai import generate_budget_insights
from apps.insights.models import MonthlyInsight
from apps.insights.services import compute_month_summary


def _parse_month(year: int, month: int):
    if month < 1 or month > 12:
        return None
    return date(year, month, 1)


def _summary_payload(month_date, summary, insight):
    return {
        "month": month_date.isoformat(),
        "total_income": summary["total_income"],
        "total_expenses": summary["total_expenses"],
        "category_totals": summary["category_totals"],
        "prior_month_category_totals": summary["prior_month_category_totals"],
        "narrative": insight.narrative if insight else None,
        "generated_at": insight.generated_at if insight else None,
    }


class InsightMonthView(APIView):
    """GET /api/insights/{year}/{month}/ - computed aggregates for that
    month plus the stored narrative, if one has been generated. Always
    200; `narrative`/`generated_at` are null until generate/ is called."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, year, month):
        month_date = _parse_month(year, month)
        if month_date is None:
            return Response({"detail": "month must be between 1 and 12."}, status=status.HTTP_400_BAD_REQUEST)

        summary = compute_month_summary(request.user, month_date)
        insight = MonthlyInsight.objects.filter(user=request.user, month=month_date).first()
        return Response(_summary_payload(month_date, summary, insight), status=status.HTTP_200_OK)


class InsightGenerateView(APIView):
    """POST /api/insights/{year}/{month}/generate/ - (re)computes aggregates
    fresh from Transaction rows, calls generate_budget_insights(), and
    creates/replaces the MonthlyInsight row for this user+month (never a
    second row for the same month - see the unique_together constraint)."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, year, month):
        month_date = _parse_month(year, month)
        if month_date is None:
            return Response({"detail": "month must be between 1 and 12."}, status=status.HTTP_400_BAD_REQUEST)

        summary = compute_month_summary(request.user, month_date)
        narrative = generate_budget_insights(
            month=month_date.strftime("%B %Y"),
            category_totals=summary["category_totals"],
            total_income=summary["total_income"],
            total_expenses=summary["total_expenses"],
            prior_month_category_totals=summary["prior_month_category_totals"],
        )

        insight, _created = MonthlyInsight.objects.update_or_create(
            user=request.user, month=month_date, defaults={"narrative": narrative},
        )

        return Response(_summary_payload(month_date, summary, insight), status=status.HTTP_200_OK)
