from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.auth_urls")),
    path("api/users/", include("apps.accounts.urls")),
    path("api/categories/", include("apps.categories.urls")),
    path("api/transactions/", include("apps.transactions.urls")),
    path("api/insights/", include("apps.insights.urls")),
]
