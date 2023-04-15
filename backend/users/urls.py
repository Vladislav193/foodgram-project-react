from django.urls import include, path
from rest_framework import routers

from api.views import UserViewSet

app_name = "users"

router = routers.DefaultRouter()
router.register("users", UserViewSet, basename="users")

urlpatterns = [
    path("api/", include(router.urls)),
    path("", include("djoser.urls")),
    path("api/auth/", include("djoser.urls.authtoken")),
]
