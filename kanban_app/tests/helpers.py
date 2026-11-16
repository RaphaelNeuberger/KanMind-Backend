"""Shared fixtures for the kanban app tests."""

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from kanban_app.models import Board, Comment, Task

User = get_user_model()


def create_user(name):
    """Create a user whose email and username are derived from ``name``."""
    email = f"{name}@example.com"
    return User.objects.create_user(
        username=email, email=email, password="pw123456",
        first_name=name.capitalize(), last_name="Tester",
    )


class KanbanTestCase(APITestCase):
    """Creates an owner, a member, an outsider, a board and a task."""

    def setUp(self):
        self.owner = create_user("owner")
        self.member = create_user("member")
        self.outsider = create_user("outsider")
        self.board = Board.objects.create(title="Project X", owner=self.owner)
        self.board.members.set([self.owner, self.member])
        self.task = Task.objects.create(
            board=self.board, title="Task 1", status="to-do",
            priority="high", assignee=self.member, reviewer=self.owner,
            created_by=self.member, due_date="2025-02-25",
        )
        self.comment = Comment.objects.create(
            task=self.task, author=self.member, content="First comment"
        )

    def login(self, user):
        """Authenticate all following requests as ``user``."""
        self.client.force_authenticate(user)
