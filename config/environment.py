import os

from django.core.exceptions import ImproperlyConfigured


def get_bool(name: str, *, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ImproperlyConfigured(f"{name} must be a boolean value.")


def get_secret_key() -> str:
    secret_key = os.environ.get("DJANGO_SECRET_KEY", "").strip()
    if not secret_key:
        raise ImproperlyConfigured("DJANGO_SECRET_KEY must be configured.")
    return secret_key


def get_int(name: str, *, default: int, minimum: int, maximum: int) -> int:
    value = os.environ.get(name)
    if value is None:
        return default

    try:
        parsed = int(value)
    except ValueError as exc:
        raise ImproperlyConfigured(f"{name} must be an integer.") from exc

    if not minimum <= parsed <= maximum:
        raise ImproperlyConfigured(f"{name} must be between {minimum} and {maximum}.")
    return parsed


def get_allowed_hosts(*, debug: bool) -> list[str]:
    value = os.environ.get("DJANGO_ALLOWED_HOSTS")
    if value is None:
        if debug:
            return ["localhost", "127.0.0.1", "[::1]"]
        raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS must be configured when DEBUG is false.")

    hosts = [host.strip() for host in value.split(",") if host.strip()]
    if not hosts:
        raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS must contain at least one host.")
    return hosts
