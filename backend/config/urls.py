from django.contrib import admin
from django.urls import include, path
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def healthz(request):
    return Response({"status": "ok"})


urlpatterns = [
    path("healthz", healthz),
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.auth_urls")),
    path("api/users/", include("apps.accounts.urls")),
    path("api/categories/", include("apps.categories.urls")),
    path("api/transactions/", include("apps.transactions.urls")),
    path("api/insights/", include("apps.insights.urls")),
]
