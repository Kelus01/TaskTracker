import json
from datetime import datetime, timezone
from io import BytesIO
from unittest.mock import patch

from django.conf import settings
from django.core.cache import cache
from django.test import SimpleTestCase
from rest_framework.test import APITestCase

from accounts.models import User
from projects.integrations.github import GitHubApiClient, GitHubApiError, GitHubCommitData
from projects.models import Project, ProjectCommit, RepositorySyncJob
from projects.repository_sync import RepositorySyncService


class GitHubApiClientTests(SimpleTestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)

    @staticmethod
    def response_body():
        return json.dumps(
            [
                {
                    "sha": "a" * 40,
                    "commit": {
                        "message": "Add task workflow",
                        "author": {"name": "Developer"},
                        "committer": {"date": "2026-11-01T10:00:00Z"},
                    },
                    "author": {"login": "developer"},
                    "html_url": "https://github.com/acme/tasks/commit/" + "a" * 40,
                }
            ]
        ).encode()

    @patch("projects.integrations.github.urlopen")
    def test_successful_response_is_cached_by_normalized_repository(self, urlopen):
        urlopen.return_value = BytesIO(self.response_body())
        client = GitHubApiClient()

        first = client.fetch_commits("Acme/Tasks")
        second = client.fetch_commits(" acme/tasks ")

        self.assertEqual(first, second)
        self.assertEqual(first[0].author, "developer")
        self.assertEqual(first[0].committed_at.tzinfo, timezone.utc)
        urlopen.assert_called_once()
        self.assertEqual(
            urlopen.call_args.kwargs["timeout"],
            settings.GITHUB_API_TIMEOUT_SECONDS,
        )

    @patch("projects.integrations.github.urlopen")
    def test_network_failure_is_reported_and_not_cached(self, urlopen):
        urlopen.side_effect = [TimeoutError, BytesIO(self.response_body())]
        client = GitHubApiClient()

        with self.assertRaises(GitHubApiError):
            client.fetch_commits("acme/tasks")
        commits = client.fetch_commits("acme/tasks")

        self.assertEqual(len(commits), 1)
        self.assertEqual(urlopen.call_count, 2)


class RepositorySyncApiTests(APITestCase):
    def setUp(self):
        manager = User.objects.create_user(
            username="sync-manager",
            password="test-password",
            role=User.Role.PROJECT_MANAGER,
        )
        self.project = Project.objects.create(
            name="GitHub project",
            manager=manager,
            github_repository="acme/tasks",
        )

    @patch("projects.integrations.github.urlopen")
    def test_sync_endpoint_queues_without_waiting_for_external_request(self, urlopen):
        response = self.client.post(
            f"/api/projects/{self.project.pk}/repository-sync/",
            format="json",
        )

        self.assertEqual(response.status_code, 202, response.data)
        job = RepositorySyncJob.objects.get(pk=response.data["id"])
        self.assertEqual(job.status, RepositorySyncJob.Status.PENDING)
        urlopen.assert_not_called()

        status_response = self.client.get(f"/api/repository-sync-jobs/{job.pk}/")
        self.assertEqual(status_response.status_code, 200)
        self.assertEqual(status_response.data["status"], "pending")

    def test_sync_requires_a_configured_github_repository(self):
        self.project.github_repository = ""
        self.project.save(update_fields=["github_repository"])

        response = self.client.post(
            f"/api/projects/{self.project.pk}/repository-sync/",
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response["Content-Type"], "application/problem+json")
        self.assertEqual(RepositorySyncJob.objects.count(), 0)

    @patch("projects.repository_sync.GitHubApiClient.fetch_commits")
    def test_worker_persists_commits_and_completes_job(self, fetch_commits):
        commit = GitHubCommitData(
            sha="b" * 40,
            message="Add background synchronization",
            author="developer",
            committed_at=datetime(2026, 11, 1, tzinfo=timezone.utc),
            html_url="https://github.com/acme/tasks/commit/" + "b" * 40,
        )
        fetch_commits.return_value = [commit]
        job = RepositorySyncService.enqueue(self.project)

        self.assertTrue(RepositorySyncService.process_next())

        job.refresh_from_db()
        self.assertEqual(job.status, RepositorySyncJob.Status.DONE)
        self.assertEqual(job.commits_synced, 1)
        self.assertEqual(ProjectCommit.objects.get(project=self.project).sha, commit.sha)
        fetch_commits.assert_called_once_with("acme/tasks")

        commits_response = self.client.get(f"/api/projects/{self.project.pk}/commits/")
        self.assertEqual(commits_response.status_code, 200)
        self.assertEqual(commits_response.data[0]["sha"], commit.sha)

    @patch("projects.repository_sync.GitHubApiClient.fetch_commits")
    def test_failed_job_does_not_prevent_processing_the_next_job(self, fetch_commits):
        first = RepositorySyncService.enqueue(self.project)
        second = RepositorySyncService.enqueue(self.project)
        fetch_commits.side_effect = [GitHubApiError("GitHub API is unavailable."), []]

        self.assertTrue(RepositorySyncService.process_next())
        self.assertTrue(RepositorySyncService.process_next())

        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(first.status, RepositorySyncJob.Status.FAILED)
        self.assertEqual(second.status, RepositorySyncJob.Status.DONE)

    def test_project_serializer_rejects_non_repository_github_values(self):
        response = self.client.patch(
            f"/api/projects/{self.project.pk}/",
            {"github_repository": "https://example.com/acme/tasks"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response["Content-Type"], "application/problem+json")
