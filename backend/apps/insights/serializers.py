from rest_framework import serializers

from apps.insights.models import MonthlyInsight


class MonthlyInsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonthlyInsight
        fields = ["id", "month", "narrative", "generated_at"]
        read_only_fields = fields
