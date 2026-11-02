from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiRequest, extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from projects.attachment_serializers import AttachmentSerializer, AttachmentUploadSerializer
from projects.filters import ProjectFilter, TaskFilter
from projects.models import Project, Task
from projects.serializers import ProjectSerializer, TaskSerializer
from projects.services import AttachmentService, ProjectService, TaskService


@extend_schema_view(
    list=extend_schema(
        summary="List projects",
        description="Повертає сторінку проєктів із фільтрацією та сортуванням.",
        tags=["Projects"],
    ),
    retrieve=extend_schema(
        summary="Retrieve project",
        description="Повертає проєкт із даними менеджера.",
        tags=["Projects"],
    ),
    create=extend_schema(
        summary="Create project",
        description=(
            "Створює проєкт. Менеджером може бути користувач із роллю admin або project_manager."
        ),
        tags=["Projects"],
    ),
    update=extend_schema(summary="Replace project", tags=["Projects"]),
    partial_update=extend_schema(summary="Update project", tags=["Projects"]),
    destroy=extend_schema(summary="Delete project", tags=["Projects"]),
)
class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    filterset_class = ProjectFilter
    ordering_fields = ["name", "created_at", "manager__username"]
    ordering = ["-created_at", "id"]

    def get_queryset(self):
        return ProjectService.list_projects()

    def perform_destroy(self, instance: Project) -> None:
        ProjectService.delete_project(instance)


@extend_schema_view(
    list=extend_schema(
        summary="List tasks",
        description="Повертає сторінку задач із вкладеними проєктом і виконавцем.",
        tags=["Tasks"],
    ),
    retrieve=extend_schema(
        summary="Retrieve task",
        description="Повертає задачу з пов'язаними проєктом і виконавцем.",
        tags=["Tasks"],
    ),
    create=extend_schema(summary="Create task", tags=["Tasks"]),
    update=extend_schema(summary="Replace task", tags=["Tasks"]),
    partial_update=extend_schema(summary="Update task", tags=["Tasks"]),
    destroy=extend_schema(summary="Delete task", tags=["Tasks"]),
)
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


class TaskAttachmentListCreateView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        summary="List task attachments",
        description="Повертає метадані файлів, доданих до задачі.",
        responses=AttachmentSerializer(many=True),
        tags=["Attachments"],
    )
    def get(self, request, task_id: int):
        task = get_object_or_404(Task, pk=task_id)
        attachments = AttachmentService.list_for_task(task)
        return Response(AttachmentSerializer(attachments, many=True).data)

    @extend_schema(
        summary="Upload task attachment",
        description="Завантажує PDF, PNG, JPEG або UTF-8 TXT розміром до 5 МБ.",
        request=OpenApiRequest(
            request=AttachmentUploadSerializer,
            encoding={
                "file": {"contentType": "application/pdf, image/png, image/jpeg, text/plain"}
            },
        ),
        responses={201: AttachmentSerializer},
        tags=["Attachments"],
    )
    def post(self, request, task_id: int):
        task = get_object_or_404(Task, pk=task_id)
        serializer = AttachmentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uploaded_file = serializer.validated_data["file"]
        attachment = AttachmentService.create(
            task=task,
            file=uploaded_file,
            original_filename=uploaded_file.name,
            content_type=uploaded_file.content_type,
            size=uploaded_file.size,
        )
        return Response(
            AttachmentSerializer(attachment).data,
            status=201,
        )


class AttachmentDownloadView(APIView):
    @extend_schema(
        summary="Download task attachment",
        description="Повертає вміст вкладеного файла.",
        responses={200: OpenApiTypes.BINARY},
        tags=["Attachments"],
    )
    def get(self, request, task_id: int, attachment_id: int):
        task = get_object_or_404(Task, pk=task_id)
        attachment = get_object_or_404(
            AttachmentService.list_for_task(task),
            pk=attachment_id,
        )
        try:
            file_handle = attachment.file.open("rb")
        except FileNotFoundError as exc:
            raise Http404("Файл вкладення не знайдено.") from exc
        return FileResponse(
            file_handle,
            as_attachment=True,
            filename=attachment.original_filename,
            content_type=attachment.content_type,
        )
