from datetime import date

from django.core.exceptions import ValidationError

from accounts.models import User
from projects.models import Project, Task
from projects.repositories import ProjectRepository, TaskRepository


class ProjectService:
    @staticmethod
    def create_project(*, name: str, description: str, manager: User) -> Project:
        if manager.role not in (User.Role.ADMIN, User.Role.PROJECT_MANAGER):
            raise ValidationError({"manager": "Користувач не може керувати проєктами."})
        return ProjectRepository.create(
            name=name,
            description=description,
            manager=manager,
        )

    @staticmethod
    def get_project(project_id: int) -> Project:
        return ProjectRepository.get_by_id(project_id)


class TaskService:
    @staticmethod
    def create_task(
        *,
        project: Project,
        title: str,
        description: str,
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
    def get_task(task_id: int) -> Task:
        return TaskRepository.get_by_id(task_id)
