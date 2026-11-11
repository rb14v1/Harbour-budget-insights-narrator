from django.conf import settings
from django.db import models


class MonthlyInsight(models.Model):
    """One AI-generated narrative per user per month. `month` always holds
    the first day of the month (e.g. 2026-11-01 means "November 2026").
    Regenerating an insight for a month replaces its narrative in place
    rather than creating a second row - see apps/insights/views.py."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="monthly_insights")
    month = models.DateField()
    narrative = models.TextField()
    generated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-month"]
        constraints = [
            models.UniqueConstraint(fields=["user", "month"], name="unique_monthly_insight_per_user_month"),
        ]

    def __str__(self):
        return f"Insight for user {self.user_id} - {self.month.isoformat()}"
