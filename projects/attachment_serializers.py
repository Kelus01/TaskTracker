from django.urls import reverse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from projects.models import Attachment
from projects.validators import validate_attachment_file


@extend_schema_field(OpenApiTypes.BINARY)
class BinaryFileField(serializers.FileField):
    pass


class AttachmentSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = Attachment
        fields = [
            "id",
            "task",
            "original_filename",
            "content_type",
            "size",
            "created_at",
            "download_url",
        ]
        read_only_fields = fields

    def get_download_url(self, attachment) -> str:
        return reverse(
            "attachment-download",
            kwargs={
                "task_id": attachment.task_id,
                "attachment_id": attachment.pk,
            },
        )


class AttachmentUploadSerializer(serializers.Serializer):
    file = BinaryFileField()

    def validate_file(self, uploaded_file):
        validate_attachment_file(uploaded_file)
        return uploaded_file
