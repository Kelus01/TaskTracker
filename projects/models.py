from pathlib import PurePath
from uuid import uuid4

from django.conf import settings
from django.db import models
from django.utils import timezone


def attachment_upload_path(instance, filename):
    extension = PurePath(filename).suffix.lower()
    return f"task_attachments/{instance.task_id}/{uuid4().hex}{extension}"


class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    github_repository = models.CharField(max_length=200, blank=True, default="")
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="managed_projects",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Task(models.Model):
    class Status(models.TextChoices):
        TODO = "todo", "До виконання"
        IN_PROGRESS = "in_progress", "У процесі"
        DONE = "done", "Виконано"

    class Priority(models.TextChoices):
        LOW = "low", "Низький"
        MEDIUM = "medium", "Середній"
        HIGH = "high", "Високий"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.TODO,
    )
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="assigned_tasks",
        null=True,
        blank=True,
    )
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        indexes = [
            models.Index(
                fields=["project", "status", "due_date", "id"],
                name="task_proj_status_due_id_idx",
            ),
        ]


class Attachment(models.Model):
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    file = models.FileField(upload_to=attachment_upload_path)
    original_filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    size = models.PositiveBigIntegerField()
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    def __str__(self):
        return self.original_filename


class ProjectCommit(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="commits",
    )
    sha = models.CharField(max_length=40)
    message = models.TextField()
    author = models.CharField(max_length=200, blank=True)
    committed_at = models.DateTimeField()
    html_url = models.URLField(max_length=500)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "sha"],
                name="project_commit_sha_unique",
            ),
        ]
        indexes = [
            models.Index(
                fields=["project", "-committed_at", "-id"],
                name="project_commit_recent_idx",
            ),
        ]

    def __str__(self):
        first_line = self.message.splitlines()[0] if self.message else ""
        return f"{self.sha[:7]} {first_line}"


class RepositorySyncJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Очікує"
        PROCESSING = "processing", "Виконується"
        DONE = "done", "Завершено"
        FAILED = "failed", "Помилка"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="repository_sync_jobs",
    )
    repository = models.CharField(max_length=200)
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.PENDING,
    )
    commits_synced = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["status", "created_at", "id"],
                name="sync_job_pending_idx",
            ),
        ]

    def __str__(self):
        return f"Repository sync {self.pk}: {self.status}"
