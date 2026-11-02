from http import HTTPStatus

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler


def problem_exception_handler(exc, context):
    if isinstance(exc, DjangoValidationError):
        detail = exc.message_dict if hasattr(exc, "message_dict") else exc.messages
        exc = ValidationError(detail)

    response = exception_handler(exc, context)
    if response is None:
        return None

    data = response.data
    title = HTTPStatus(response.status_code).phrase
    if isinstance(data, dict) and "detail" in data:
        detail = str(data["detail"])
        errors = {key: value for key, value in data.items() if key != "detail"}
    else:
        detail = "Request validation failed."
        errors = data

    response.data = {
        "type": "about:blank",
        "title": title,
        "status": response.status_code,
        "detail": detail,
    }
    if errors:
        response.data["errors"] = errors
    response.content_type = "application/problem+json"
    return response
