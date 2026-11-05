import logging

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from projects.integrations.github import GitHubApiClient, GitHubApiError
from projects.models import Project, ProjectCommit, RepositorySyncJob

logger = logging.getLogger(__name__)


class RepositorySyncService:
    @staticmethod
    def enqueue(project: Project) -> RepositorySyncJob:
        repository = project.github_repository.strip()
        if not repository:
            raise ValidationError(
                {"github_repository": "Спочатку вкажіть GitHub-репозиторій проєкту."}
            )
        return RepositorySyncJob.objects.create(
            project=project,
            repository=repository,
        )

    @classmethod
    def process_next(cls) -> bool:
        job_id = (
            RepositorySyncJob.objects.filter(status=RepositorySyncJob.Status.PENDING)
            .order_by("created_at", "id")
            .values_list("id", flat=True)
            .first()
        )
        if job_id is None:
            return False

        with transaction.atomic():
            claimed = RepositorySyncJob.objects.filter(
                pk=job_id,
                status=RepositorySyncJob.Status.PENDING,
            ).update(
                status=RepositorySyncJob.Status.PROCESSING,
                started_at=timezone.now(),
            )
        if not claimed:
            return False

        job = RepositorySyncJob.objects.select_related("project").get(pk=job_id)
        try:
            commits = GitHubApiClient().fetch_commits(job.repository)
            with transaction.atomic():
                for commit in commits:
                    ProjectCommit.objects.update_or_create(
                        project=job.project,
                        sha=commit.sha,
                        defaults={
                            "message": commit.message,
                            "author": commit.author,
                            "committed_at": commit.committed_at,
                            "html_url": commit.html_url,
                        },
                    )
                job.status = RepositorySyncJob.Status.DONE
                job.commits_synced = len(commits)
                job.completed_at = timezone.now()
                job.save(
                    update_fields=[
                        "status",
                        "commits_synced",
                        "completed_at",
                    ]
                )
        except GitHubApiError as exc:
            cls._mark_failed(job, str(exc))
        except Exception:
            logger.exception("Unexpected error while processing repository sync job %s.", job.pk)
            cls._mark_failed(job, "Repository synchronization failed unexpectedly.")
        return True

    @staticmethod
    def _mark_failed(job: RepositorySyncJob, message: str) -> None:
        job.status = RepositorySyncJob.Status.FAILED
        job.error_message = message
        job.completed_at = timezone.now()
        job.save(update_fields=["status", "error_message", "completed_at"])
