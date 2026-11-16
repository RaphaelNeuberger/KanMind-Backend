"""API views for boards, tasks and comments."""

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from kanban_app.models import Board, Comment, Task

from .permissions import (
    IsBoardMemberOrOwner,
    IsBoardOwner,
    IsCommentAuthor,
    IsTaskCreatorOrBoardOwner,
)
from .serializers import (
    BoardDetailSerializer,
    BoardListSerializer,
    BoardUpdateSerializer,
    CommentSerializer,
    TaskCreateSerializer,
    TaskSerializer,
    TaskUpdateSerializer,
)


class BoardViewSet(viewsets.ModelViewSet):
    """List, create, retrieve, update and delete boards."""

    queryset = Board.objects.all()
    serializer_class = BoardListSerializer
    permission_classes = [IsAuthenticated & IsBoardMemberOrOwner]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    serializer_classes = {
        "retrieve": BoardDetailSerializer,
        "partial_update": BoardUpdateSerializer,
    }

    def get_queryset(self):
        """Limit the board list to boards the user owns or is member of."""
        if self.action != "list":
            return self.queryset
        user = self.request.user
        return self.queryset.filter(
            Q(owner=user) | Q(members=user)
        ).distinct()

    def get_serializer_class(self):
        """Pick the serializer that matches the current action."""
        return self.serializer_classes.get(self.action, self.serializer_class)

    def get_permissions(self):
        """Only the board owner may delete a board."""
        if self.action == "destroy":
            return [IsAuthenticated(), IsBoardOwner()]
        return super().get_permissions()

    def perform_create(self, serializer):
        """Store the requesting user as owner of the new board."""
        serializer.save(owner=self.request.user)


class TaskViewSet(mixins.CreateModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.DestroyModelMixin,
                  viewsets.GenericViewSet):
    """Create, partially update and delete tasks."""

    queryset = Task.objects.select_related("board")
    serializer_class = TaskCreateSerializer
    permission_classes = [IsAuthenticated & IsBoardMemberOrOwner]
    http_method_names = ["post", "patch", "delete", "options"]

    def get_serializer_class(self):
        """Use a dedicated serializer for partial updates."""
        if self.action == "partial_update":
            return TaskUpdateSerializer
        return self.serializer_class

    def get_permissions(self):
        """Only the task creator or the board owner may delete a task."""
        if self.action == "destroy":
            return [IsAuthenticated(), IsTaskCreatorOrBoardOwner()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        """Check access to the target board before creating the task."""
        self.check_board_access(request.data.get("board"))
        return super().create(request, *args, **kwargs)

    def check_board_access(self, board_id):
        """Raise 404 for an unknown board and 403 for non-members."""
        if str(board_id).isdigit():
            board = get_object_or_404(Board, pk=board_id)
            self.check_object_permissions(self.request, board)

    def perform_create(self, serializer):
        """Store the requesting user as creator of the task."""
        serializer.save(created_by=self.request.user)


class AssignedTaskListView(generics.ListAPIView):
    """GET /api/tasks/assigned-to-me/ - tasks assigned to the user."""

    queryset = Task.objects.select_related("assignee", "reviewer")
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return only the tasks where the user is the assignee."""
        return self.queryset.filter(assignee=self.request.user)


class ReviewingTaskListView(AssignedTaskListView):
    """GET /api/tasks/reviewing/ - tasks the user has to review."""

    def get_queryset(self):
        """Return only the tasks where the user is the reviewer."""
        return self.queryset.filter(reviewer=self.request.user)


class TaskCommentMixin:
    """Shared lookup of the task a comment endpoint refers to."""

    def initial(self, request, *args, **kwargs):
        """Resolve the task before the request is handled."""
        super().initial(request, *args, **kwargs)
        self.task = self.get_task()

    def get_task(self):
        """Return the task from the URL or raise 404/403."""
        task = get_object_or_404(
            Task.objects.select_related("board"), pk=self.kwargs["task_id"]
        )
        if not IsBoardMemberOrOwner().has_object_permission(
            self.request, self, task
        ):
            self.permission_denied(
                self.request, message=IsBoardMemberOrOwner.message
            )
        return task


class CommentListCreateView(TaskCommentMixin, generics.ListCreateAPIView):
    """List and create the comments of a task."""

    queryset = Comment.objects.select_related("author")
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return the comments of the task in chronological order."""
        return self.queryset.filter(task=self.task)

    def perform_create(self, serializer):
        """Attach the comment to the task and the requesting user."""
        serializer.save(task=self.task, author=self.request.user)


class CommentDeleteView(TaskCommentMixin, generics.DestroyAPIView):
    """Delete a single comment of a task."""

    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated & IsCommentAuthor]

    def get_queryset(self):
        """Only look up comments that belong to the task in the URL."""
        return self.queryset.filter(task=self.task)
