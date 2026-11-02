from rest_framework import viewsets

from projects.filters import ProjectFilter, TaskFilter
from projects.models import Project, Task
from projects.serializers import ProjectSerializer, TaskSerializer
from projects.services import ProjectService, TaskService


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    filterset_class = ProjectFilter
    ordering_fields = ["name", "created_at", "manager__username"]
    ordering = ["-created_at", "id"]

    def get_queryset(self):
        return ProjectService.list_projects()

    def perform_destroy(self, instance: Project) -> None:
        ProjectService.delete_project(instance)


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    filterset_class = TaskFilter
    ordering_fields = [
        "title",
        "status",
        "priority",
        "due_date",
        "created_at",
        "updated_at",
    ]
    ordering = ["-created_at", "id"]

    def get_queryset(self):
        return TaskService.list_tasks()

    def perform_destroy(self, instance: Task) -> None:
        TaskService.delete_task(instance)
