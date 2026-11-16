"""Admin configuration for boards, tasks and comments."""

from django.contrib import admin

from .models import Board, Comment, Task


class TaskInline(admin.TabularInline):
    """Shows the tasks of a board directly on the board page."""

    model = Task
    extra = 0
    fields = ["title", "status", "priority", "assignee", "due_date"]


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    """Admin view for boards."""

    list_display = ["id", "title", "owner", "created_at"]
    search_fields = ["title", "owner__email"]
    filter_horizontal = ["members"]
    inlines = [TaskInline]


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Admin view for tasks."""

    list_display = [
        "id", "title", "board", "status", "priority", "assignee", "due_date",
    ]
    list_filter = ["status", "priority", "board"]
    search_fields = ["title", "description"]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Admin view for comments."""

    list_display = ["id", "task", "author", "created_at"]
    search_fields = ["content", "author__email"]
