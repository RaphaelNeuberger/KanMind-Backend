"""App configuration of the kanban app."""

from django.apps import AppConfig


class KanbanAppConfig(AppConfig):
    """Boards, tasks and comments."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "kanban_app"
    verbose_name = "Kanban"
