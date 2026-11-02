from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from config.views import health
from projects.views import ProjectViewSet, TaskViewSet

router = DefaultRouter()
router.register("projects", ProjectViewSet, basename="project")
router.register("tasks", TaskViewSet, basename="task")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health", health, name="health"),
    path("api/", include(router.urls)),
]
