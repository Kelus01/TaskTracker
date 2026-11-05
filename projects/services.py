from datetime import date

from django.core.exceptions import ValidationError
from django.db.models import QuerySet

from accounts.models import User
from projects.models import Attachment, Project, Task
from projects.repositories import AttachmentRepository, ProjectRepository, TaskRepository


class ProjectService:
    @staticmethod
    def list_projects() -> QuerySet[Project]:
        return ProjectRepository.list()

    @staticmethod
    def create_project(
        *,
        name: str,
        manager: User,
        description: str = "",
        github_repository: str = "",
    ) -> Project:
        if manager.role not in (User.Role.ADMIN, User.Role.PROJECT_MANAGER):
            raise ValidationError({"manager": "Користувач не може керувати проєктами."})
        return ProjectRepository.create(
            name=name,
            description=description,
            github_repository=github_repository,
            manager=manager,
        )

    @staticmethod
    def update_project(project: Project, **fields) -> Project:
        manager = fields.get("manager")
        if manager and manager.role not in (User.Role.ADMIN, User.Role.PROJECT_MANAGER):
            raise ValidationError({"manager": "Користувач не може керувати проєктами."})
        return ProjectRepository.update(project, **fields)

    @staticmethod
    def get_project(project_id: int) -> Project:
        return ProjectRepository.get_by_id(project_id)

    @staticmethod
    def delete_project(project: Project) -> None:
        ProjectRepository.delete(project)


class TaskService:
    @staticmethod
    def list_tasks() -> QuerySet[Task]:
        return TaskRepository.list()

    @staticmethod
    def create_task(
        *,
        project: Project,
        title: str,
        description: str = "",
        status: str = Task.Status.TODO,
        priority: str = Task.Priority.MEDIUM,
        assignee: User | None = None,
        due_date: date | None = None,
    ) -> Task:
        return TaskRepository.create(
            project=project,
            title=title,
            description=description,
            status=status,
            priority=priority,
            assignee=assignee,
            due_date=due_date,
        )

    @staticmethod
    def update_task(task: Task, **fields) -> Task:
        return TaskRepository.update(task, **fields)

    @staticmethod
    def get_task(task_id: int) -> Task:
        return TaskRepository.get_by_id(task_id)

    @staticmethod
    def delete_task(task: Task) -> None:
        TaskRepository.delete(task)


class AttachmentService:
    @staticmethod
    def list_for_task(task: Task) -> QuerySet[Attachment]:
        return AttachmentRepository.list_for_task(task)

    @staticmethod
    def create(
        *,
        task: Task,
        file,
        original_filename: str,
        content_type: str,
        size: int,
    ) -> Attachment:
        return AttachmentRepository.create(
            task=task,
            file=file,
            original_filename=original_filename,
            content_type=content_type,
            size=size,
        )

    @staticmethod
    def get_for_task(*, task: Task, attachment_id: int) -> Attachment:
        return AttachmentRepository.get_for_task(task=task, attachment_id=attachment_id)
