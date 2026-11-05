import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0002_attachment"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ProjectCommit",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("sha", models.CharField(max_length=40)),
                ("message", models.TextField()),
                ("author", models.CharField(blank=True, max_length=200)),
                ("committed_at", models.DateTimeField()),
                ("html_url", models.URLField(max_length=500)),
            ],
        ),
        migrations.CreateModel(
            name="RepositorySyncJob",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("repository", models.CharField(max_length=200)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Очікує"),
                            ("processing", "Виконується"),
                            ("done", "Завершено"),
                            ("failed", "Помилка"),
                        ],
                        default="pending",
                        max_length=12,
                    ),
                ),
                ("commits_synced", models.PositiveIntegerField(default=0)),
                ("error_message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.AddField(
            model_name="project",
            name="github_repository",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
        migrations.AddIndex(
            model_name="task",
            index=models.Index(
                fields=["project", "status", "due_date", "id"], name="task_proj_status_due_id_idx"
            ),
        ),
        migrations.AddField(
            model_name="projectcommit",
            name="project",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="commits",
                to="projects.project",
            ),
        ),
        migrations.AddField(
            model_name="repositorysyncjob",
            name="project",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="repository_sync_jobs",
                to="projects.project",
            ),
        ),
        migrations.AddIndex(
            model_name="projectcommit",
            index=models.Index(
                fields=["project", "-committed_at", "-id"], name="project_commit_recent_idx"
            ),
        ),
        migrations.AddConstraint(
            model_name="projectcommit",
            constraint=models.UniqueConstraint(
                fields=("project", "sha"), name="project_commit_sha_unique"
            ),
        ),
        migrations.AddIndex(
            model_name="repositorysyncjob",
            index=models.Index(fields=["status", "created_at", "id"], name="sync_job_pending_idx"),
        ),
    ]
