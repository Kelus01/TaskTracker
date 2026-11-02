import os
from pathlib import Path

from config.environment import get_allowed_hosts, get_bool, get_secret_key

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = get_secret_key()
DEBUG = get_bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = get_allowed_hosts(debug=DEBUG)

database_path = Path(os.environ.get("DJANGO_DB_PATH", "db.sqlite3"))
if not database_path.is_absolute():
    database_path = BASE_DIR / database_path

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_filters",
    "drf_spectacular",
    "accounts",
    "projects",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": database_path,
        "TEST": {
            "NAME": BASE_DIR / "test_db.sqlite3",
        },
    }
}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "uk"
TIME_ZONE = "Europe/Kyiv"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": [
        "projects.filters.StrictDjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "config.exceptions.problem_exception_handler",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Task Tracker API",
    "DESCRIPTION": "API для керування проєктами, задачами та вкладеннями.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

MAX_ATTACHMENT_SIZE = 5 * 1024 * 1024
