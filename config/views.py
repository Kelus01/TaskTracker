from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response


@extend_schema(
    summary="Health check",
    description="Перевіряє, що застосунок обробляє запити.",
    responses={200: OpenApiTypes.OBJECT},
    tags=["System"],
)
@api_view(["GET"])
def health(request):
    return Response({"status": "ok"})
