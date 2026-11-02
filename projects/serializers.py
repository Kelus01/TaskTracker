from rest_framework import serializers

from accounts.models import User
from projects.models import Project, Task
from projects.services import ProjectService, TaskService


class UserSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "role"]
        read_only_fields = fields


class ProjectSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "name"]
        read_only_fields = fields


class ProjectSerializer(serializers.ModelSerializer):
    manager = UserSummarySerializer(read_only=True)
    manager_id = serializers.PrimaryKeyRelatedField(
        source="manager",
        queryset=User.objects.all(),
        write_only=True,
    )

    class Meta:
        model = Project
        fields = ["id", "name", "description", "manager", "manager_id", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_manager_id(self, manager):
        if manager.role not in (User.Role.ADMIN, User.Role.PROJECT_MANAGER):
            raise serializers.ValidationError("Користувач не може керувати проєктами.")
        return manager

    def create(self, validated_data):
        return ProjectService.create_project(**validated_data)

    def update(self, instance, validated_data):
        return ProjectService.update_project(instance, **validated_data)


class TaskSerializer(serializers.ModelSerializer):
    project = ProjectSummarySerializer(read_only=True)
    project_id = serializers.PrimaryKeyRelatedField(
        source="project",
        queryset=Project.objects.all(),
        write_only=True,
    )
    assignee = UserSummarySerializer(read_only=True)
    assignee_id = serializers.PrimaryKeyRelatedField(
        source="assignee",
        queryset=User.objects.all(),
        required=False,
        allow_null=True,
        write_only=True,
    )

    class Meta:
        model = Task
        fields = [
            "id",
            "project",
            "project_id",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "assignee_id",
            "due_date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        return TaskService.create_task(**validated_data)

    def update(self, instance, validated_data):
        return TaskService.update_task(instance, **validated_data)
