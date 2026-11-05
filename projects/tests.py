import json
import tempfile
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase

from accounts.models import User
from projects.models import Attachment, Project, Task


class ProjectTaskApiTests(APITestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="api-manager",
            password="test-password",
            role=User.Role.PROJECT_MANAGER,
        )
        self.member = User.objects.create_user(
            username="api-member",
            password="test-password",
            role=User.Role.MEMBER,
        )

    def create_project(self, name="API project"):
        response = self.client.post(
            "/api/projects/",
            {"name": name, "description": "Project description", "manager_id": self.manager.pk},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        return response.data

    def test_project_and_task_crud_persist_related_data(self):
        project_data = self.create_project()
        project = Project.objects.get(pk=project_data["id"])
        self.assertEqual(project.manager, self.manager)

        task_response = self.client.post(
            "/api/tasks/",
            {
                "project_id": project.pk,
                "title": "API task",
                "description": "Task description",
                "status": "in_progress",
                "priority": "high",
                "assignee_id": self.member.pk,
            },
            format="json",
        )
        self.assertEqual(task_response.status_code, 201, task_response.data)
        task_id = task_response.data["id"]
        self.assertEqual(task_response.data["project"]["id"], project.pk)
        self.assertEqual(task_response.data["assignee"]["id"], self.member.pk)
        task = Task.objects.get(pk=task_id)
        self.assertEqual(task.project, project)
        self.assertEqual(task.assignee, self.member)

        detail_response = self.client.get(f"/api/tasks/{task_id}/")
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.data["project"]["name"], project.name)

        update_response = self.client.patch(
            f"/api/tasks/{task_id}/",
            {"status": "done"},
            format="json",
        )
        self.assertEqual(update_response.status_code, 200)
        task.refresh_from_db()
        self.assertEqual(task.status, Task.Status.DONE)

        delete_response = self.client.delete(f"/api/tasks/{task_id}/")
        self.assertEqual(delete_response.status_code, 204)
        self.assertFalse(Task.objects.filter(pk=task_id).exists())

        project_update = self.client.patch(
            f"/api/projects/{project.pk}/",
            {"name": "Updated project"},
            format="json",
        )
        self.assertEqual(project_update.status_code, 200)
        project.refresh_from_db()
        self.assertEqual(project.name, "Updated project")

        project_delete = self.client.delete(f"/api/projects/{project.pk}/")
        self.assertEqual(project_delete.status_code, 204)
        self.assertFalse(Project.objects.filter(pk=project.pk).exists())

    def test_task_list_supports_pagination_filtering_and_ordering(self):
        project_data = self.create_project()
        project = Project.objects.get(pk=project_data["id"])
        Task.objects.bulk_create(
            [
                Task(
                    project=project,
                    title=f"Task {index:02}",
                    status=Task.Status.TODO if index % 2 else Task.Status.DONE,
                    priority=Task.Priority.MEDIUM,
                )
                for index in range(21)
            ]
        )

        first_page = self.client.get("/api/tasks/?ordering=title")
        self.assertEqual(first_page.status_code, 200)
        self.assertEqual(first_page.data["count"], 21)
        self.assertEqual(len(first_page.data["results"]), 20)
        self.assertEqual(first_page.data["results"][0]["title"], "Task 00")

        second_page = self.client.get("/api/tasks/?ordering=title&page=2")
        self.assertEqual(second_page.status_code, 200)
        self.assertEqual(len(second_page.data["results"]), 1)

        filtered = self.client.get("/api/tasks/?project={}&status=done".format(project.pk))
        self.assertEqual(filtered.status_code, 200)
        self.assertEqual(filtered.data["count"], 11)

    def test_project_status_due_date_query_uses_composite_index(self):
        project = Project.objects.create(name="Indexed project", manager=self.manager)

        query = Task.objects.filter(
            project=project,
            status=Task.Status.TODO,
        ).order_by("due_date", "id")

        self.assertIn("task_proj_status_due_id_idx", query.explain())

    def test_invalid_input_returns_problem_details(self):
        response = self.client.post(
            "/api/projects/",
            {"name": "", "manager_id": self.member.pk},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response["Content-Type"], "application/problem+json")
        self.assertEqual(response.data["status"], 400)
        self.assertIn("errors", response.data)

        missing = self.client.get("/api/tasks/999999/")
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(missing["Content-Type"], "application/problem+json")


class AttachmentApiTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.media_directory = tempfile.TemporaryDirectory()
        cls.media_override = override_settings(MEDIA_ROOT=cls.media_directory.name)
        cls.media_override.enable()

    @classmethod
    def tearDownClass(cls):
        cls.media_override.disable()
        cls.media_directory.cleanup()
        super().tearDownClass()

    def setUp(self):
        manager = User.objects.create_user(
            username="attachment-manager",
            password="test-password",
            role=User.Role.PROJECT_MANAGER,
        )
        project = Project.objects.create(name="Attachment project", manager=manager)
        self.task = Task.objects.create(project=project, title="Attachment task")

    def test_upload_list_and_download_attachment(self):
        file_content = b"%PDF-1.4\nTask attachment"
        upload = SimpleUploadedFile(
            "report.pdf",
            file_content,
            content_type="application/pdf",
        )
        response = self.client.post(
            f"/api/tasks/{self.task.pk}/attachments/",
            {"file": upload},
            format="multipart",
        )
        self.assertEqual(response.status_code, 201, response.data)
        attachment = Attachment.objects.get(pk=response.data["id"])
        self.assertEqual(attachment.task, self.task)
        self.assertEqual(attachment.original_filename, "report.pdf")
        self.assertTrue(Path(attachment.file.path).is_file())

        listing = self.client.get(f"/api/tasks/{self.task.pk}/attachments/")
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(listing.data[0]["id"], attachment.pk)

        download = self.client.get(response.data["download_url"])
        self.assertEqual(download.status_code, 200)
        self.assertEqual(download["Content-Type"], "application/pdf")
        self.assertIn('filename="report.pdf"', download["Content-Disposition"])
        self.assertEqual(b"".join(download.streaming_content), file_content)

    def test_upload_rejects_unsupported_and_oversized_files(self):
        unsupported = SimpleUploadedFile(
            "script.exe",
            b"not allowed",
            content_type="application/octet-stream",
        )
        response = self.client.post(
            f"/api/tasks/{self.task.pk}/attachments/",
            {"file": unsupported},
            format="multipart",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response["Content-Type"], "application/problem+json")
        self.assertEqual(Attachment.objects.count(), 0)

        oversized = SimpleUploadedFile(
            "large.pdf",
            b"%PDF-" + b"x" * (5 * 1024 * 1024),
            content_type="application/pdf",
        )
        response = self.client.post(
            f"/api/tasks/{self.task.pk}/attachments/",
            {"file": oversized},
            format="multipart",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Attachment.objects.count(), 0)

    def test_upload_rejects_mismatched_file_content(self):
        invalid_pdf = SimpleUploadedFile(
            "report.pdf",
            b"This is not a PDF",
            content_type="application/pdf",
        )
        response = self.client.post(
            f"/api/tasks/{self.task.pk}/attachments/",
            {"file": invalid_pdf},
            format="multipart",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Attachment.objects.count(), 0)

    def test_deleting_task_removes_attached_file(self):
        upload = SimpleUploadedFile(
            "report.pdf",
            b"%PDF-1.4\nTask attachment",
            content_type="application/pdf",
        )
        response = self.client.post(
            f"/api/tasks/{self.task.pk}/attachments/",
            {"file": upload},
            format="multipart",
        )
        self.assertEqual(response.status_code, 201, response.data)
        attachment = Attachment.objects.get(pk=response.data["id"])
        stored_path = Path(attachment.file.path)
        self.assertTrue(stored_path.is_file())

        self.task.delete()

        self.assertFalse(Attachment.objects.filter(pk=attachment.pk).exists())
        self.assertFalse(stored_path.exists())


class ApiDocumentationTests(APITestCase):
    def test_openapi_schema_and_swagger_ui_are_available(self):
        schema_response = self.client.get("/api/schema/?format=json")
        self.assertEqual(schema_response.status_code, 200)
        schema = json.loads(schema_response.content)
        self.assertEqual(schema["openapi"], "3.0.3")
        self.assertIn("/api/projects/", schema["paths"])
        self.assertIn("/api/tasks/", schema["paths"])
        self.assertIn("/api/tasks/{task_id}/attachments/", schema["paths"])
        self.assertIn("/api/tasks/{task_id}/attachments/{attachment_id}/download/", schema["paths"])
        upload_schema = schema["components"]["schemas"]["AttachmentUpload"]
        self.assertEqual(upload_schema["properties"]["file"]["format"], "binary")

        docs_response = self.client.get("/api/docs/")
        self.assertEqual(docs_response.status_code, 200)
        self.assertContains(docs_response, "SwaggerUIBundle")
