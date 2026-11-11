from django.urls import path

from apps.insights.views import InsightGenerateView, InsightMonthView

urlpatterns = [
    path("<int:year>/<int:month>/", InsightMonthView.as_view(), name="insight-month"),
    path("<int:year>/<int:month>/generate/", InsightGenerateView.as_view(), name="insight-generate"),
]
