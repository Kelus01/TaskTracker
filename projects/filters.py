import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import ValidationError

from projects.models import Project, Task


class StrictDjangoFilterBackend(DjangoFilterBackend):
    def filter_queryset(self, request, queryset, view):
        filterset = self.get_filterset(request, queryset, view)
        if filterset is None:
            return queryset
        if not filterset.is_valid():
            raise ValidationError(filterset.errors)
        return filterset.qs


class ProjectFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    manager = django_filters.NumberFilter(field_name="manager_id")
    created_after = django_filters.IsoDateTimeFilter(
        field_name="created_at",
        lookup_expr="gte",
    )
    created_before = django_filters.IsoDateTimeFilter(
        field_name="created_at",
        lookup_expr="lte",
    )

    class Meta:
        model = Project
        fields = ["name", "manager", "created_after", "created_before"]


class TaskFilter(django_filters.FilterSet):
    project = django_filters.NumberFilter(field_name="project_id")
    assignee = django_filters.NumberFilter(field_name="assignee_id")
    due_after = django_filters.DateFilter(field_name="due_date", lookup_expr="gte")
    due_before = django_filters.DateFilter(field_name="due_date", lookup_expr="lte")

    class Meta:
        model = Task
        fields = ["project", "status", "priority", "assignee", "due_after", "due_before"]
