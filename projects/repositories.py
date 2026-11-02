from datetime import date

from accounts.models import User
from projects.models import Project, Task


class ProjectRepository:
    @staticmethod
    def create(*, name: str, description: str, manager: User) -> Project:
        return Project.objects.create(
            name=name,
            description=description,
            manager=manager,
        )

    @staticmethod
    def get_by_id(project_id: int) -> Project:
        return Project.objects.get(pk=project_id)


class TaskRepository:
    @staticmethod
    def create(
        *,
        project: Project,
        title: str,
        description: str,
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
        return Task.objects.get(pk=task_id)
