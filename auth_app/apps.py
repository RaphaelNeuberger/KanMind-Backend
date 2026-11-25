"""App configuration of the auth app."""

from django.apps import AppConfig


class AuthAppConfig(AppConfig):
    """Registration, login and email check."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "auth_app"
    verbose_name = "Authentication"
