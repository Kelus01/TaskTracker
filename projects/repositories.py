from datetime import date

from django.db import models

from accounts.models import User
from projects.models import Project, Task


class ProjectRepository:
    @staticmethod
    def list() -> models.QuerySet[Project]:
        return Project.objects.select_related("manager")

    @staticmethod
    def create(*, name: str, manager: User, description: str = "") -> Project:
        return Project.objects.create(
            name=name,
            description=description,
            manager=manager,
        )

    @staticmethod
    def get_by_id(project_id: int) -> Project:
        return Project.objects.select_related("manager").get(pk=project_id)

    @staticmethod
    def update(project: Project, **fields) -> Project:
        for field, value in fields.items():
            setattr(project, field, value)
        if fields:
            project.save(update_fields=list(fields))
        return project

    @staticmethod
    def delete(project: Project) -> None:
        project.delete()


class TaskRepository:
    @staticmethod
    def list() -> models.QuerySet[Task]:
        return Task.objects.select_related("project", "assignee")

    @staticmethod
    def create(
        *,
        project: Project,
        title: str,
        description: str = "",
        status: str = Task.Status.TODO,
        priority: str = Task.Priority.MEDIUM,
        assignee: User | None = None,
        due_date: date | None = None,
    ) -> Task:
        return Task.objects.create(
            project=project,
            title=title,
            description=description,
            status=status,
            priority=priority,
            assignee=assignee,
            due_date=due_date,
        )

    @staticmethod
    def get_by_id(task_id: int) -> Task:
        return Task.objects.select_related("project", "assignee").get(pk=task_id)

    @staticmethod
    def update(task: Task, **fields) -> Task:
        for field, value in fields.items():
            setattr(task, field, value)
        if fields:
            task.save(update_fields=[*fields, "updated_at"])
        return task

    @staticmethod
    def delete(task: Task) -> None:
        task.delete()
