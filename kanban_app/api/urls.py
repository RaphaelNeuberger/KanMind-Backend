"""URL routes of the kanban app."""

from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import (
    AssignedTaskListView,
    BoardViewSet,
    CommentDeleteView,
    CommentListCreateView,
    ReviewingTaskListView,
    TaskViewSet,
)

router = SimpleRouter()
# Accept URLs with and without trailing slash (the frontend uses both).
router.trailing_slash = "/?"
router.register("boards", BoardViewSet, basename="board")
router.register("tasks", TaskViewSet, basename="task")

urlpatterns = [
    path(
        "tasks/assigned-to-me/",
        AssignedTaskListView.as_view(),
        name="tasks-assigned-to-me",
    ),
    path(
        "tasks/reviewing/",
        ReviewingTaskListView.as_view(),
        name="tasks-reviewing",
    ),
    path(
        "tasks/<int:task_id>/comments/",
        CommentListCreateView.as_view(),
        name="task-comments",
    ),
    path(
        "tasks/<int:task_id>/comments/<int:pk>/",
        CommentDeleteView.as_view(),
        name="task-comment-detail",
    ),
    path("", include(router.urls)),
]
