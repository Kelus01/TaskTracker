from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Адміністратор"
        PROJECT_MANAGER = "project_manager", "Менеджер проєкту"
        MEMBER = "member", "Учасник"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
    )
