from pathlib import PurePath

from django.conf import settings
from rest_framework import serializers

ALLOWED_CONTENT_TYPES = {
    ".jpeg": "image/jpeg",
    ".jpg": "image/jpeg",
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".txt": "text/plain",
}


def validate_attachment_file(uploaded_file):
    extension = PurePath(uploaded_file.name).suffix.lower()
    expected_content_type = ALLOWED_CONTENT_TYPES.get(extension)
    if expected_content_type is None:
        raise serializers.ValidationError("Дозволені формати: PDF, PNG, JPEG і TXT.")

    if uploaded_file.size > settings.MAX_ATTACHMENT_SIZE:
        raise serializers.ValidationError(
            f"Максимальний розмір файла — {settings.MAX_ATTACHMENT_SIZE // (1024 * 1024)} МБ."
        )

    if uploaded_file.content_type != expected_content_type:
        raise serializers.ValidationError("Тип файла не відповідає його розширенню.")

    content = uploaded_file.read()
    uploaded_file.seek(0)

    if extension == ".pdf" and not content.startswith(b"%PDF-"):
        raise serializers.ValidationError("Файл не є коректним PDF.")
    if extension == ".png" and not content.startswith(b"\x89PNG\r\n\x1a\n"):
        raise serializers.ValidationError("Файл не є коректним PNG.")
    if extension in {".jpg", ".jpeg"} and not content.startswith(b"\xff\xd8\xff"):
        raise serializers.ValidationError("Файл не є коректним JPEG.")
    if extension == ".txt":
        try:
            content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise serializers.ValidationError("Текстовий файл має бути у форматі UTF-8.") from exc
        if b"\x00" in content:
            raise serializers.ValidationError("Текстовий файл містить недопустимі дані.")

    return expected_content_type
