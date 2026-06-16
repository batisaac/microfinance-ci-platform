from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

api_prefix = "api/v1/"

urlpatterns = [
    path("", include("apps.frontend.urls")),
    path("favicon.ico", lambda r: HttpResponse(status=204)),
    path("admin/", admin.site.urls),
    path(f"{api_prefix}auth/", include("apps.accounts.urls")),
    path(f"{api_prefix}loans/", include("apps.credits.urls")),
    path(f"{api_prefix}repayments/", include("apps.repayments.urls")),
    path(f"{api_prefix}insurance/", include("apps.insurance.urls")),
    path(f"{api_prefix}notifications/", include("apps.notifications.urls")),
    path(f"{api_prefix}chat/", include("apps.chat.urls")),
    path(f"{api_prefix}dashboard/", include("apps.dashboard.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
