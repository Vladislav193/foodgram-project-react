from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("api.urls", namespace="api")),
    path("", include("users.urls", namespace="users")),
]
