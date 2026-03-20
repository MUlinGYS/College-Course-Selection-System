from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("users.urls")),
    path("api/", include("rounds.urls")),
    path("api/", include("courses.urls")),
    path("api/", include("enrollments.urls")),
    path(
        "api/health/",
        lambda request: JsonResponse({"ok": True}),
        name="health",
    ),
]
