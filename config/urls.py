from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from config.views import health
from projects.views import (
    AttachmentDownloadView,
    ProjectViewSet,
    RepositorySyncJobDetailView,
    TaskAttachmentListCreateView,
    TaskViewSet,
)

router = DefaultRouter()
router.register("projects", ProjectViewSet, basename="project")
router.register("tasks", TaskViewSet, basename="task")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health", health, name="health"),
    path("api/", include(router.urls)),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/tasks/<int:task_id>/attachments/",
        TaskAttachmentListCreateView.as_view(),
        name="task-attachments",
    ),
    path(
        "api/tasks/<int:task_id>/attachments/<int:attachment_id>/download/",
        AttachmentDownloadView.as_view(),
        name="attachment-download",
    ),
    path(
        "api/repository-sync-jobs/<int:job_id>/",
        RepositorySyncJobDetailView.as_view(),
        name="repository-sync-job-detail",
    ),
]
