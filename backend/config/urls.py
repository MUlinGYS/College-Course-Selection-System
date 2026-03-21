from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from core.frontend import serve_frontend

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(permission_classes=[]), name="schema"),
    path(
        "swagger/",
        SpectacularSwaggerView.as_view(url_name="schema", permission_classes=[]),
        name="swagger-ui",
    ),
    path(
        "redoc/",
        SpectacularRedocView.as_view(url_name="schema", permission_classes=[]),
        name="redoc",
    ),
    path("api/", include("users.urls")),
    path("api/", include("rounds.urls")),
    path("api/", include("courses.urls")),
    path("api/", include("applications.urls")),
    path("api/", include("enrollments.urls")),
    path(
        "api/health/",
        lambda request: JsonResponse({"ok": True}),
        name="health",
    ),
    path("", serve_frontend, name="frontend-root"),
    re_path(r"^(?!api/|django-admin/|swagger/|redoc/)(?P<path>.*)$", serve_frontend, name="frontend"),
]
