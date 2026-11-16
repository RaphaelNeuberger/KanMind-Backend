"""Tests for the task endpoints."""

from django.urls import reverse
from rest_framework import status

from kanban_app.models import Board, Task

from .helpers import KanbanTestCase

TASK_DATA = {
    "title": "Code review",
    "description": "Review the new PR",
    "status": "review",
    "priority": "medium",
    "due_date": "2025-02-27",
}


class TaskCreateTests(KanbanTestCase):
    """POST /api/tasks/"""

    url = reverse("task-list")

    def payload(self, **extra):
        return {**TASK_DATA, "board": self.board.id, **extra}

    def test_member_creates_task(self):
        self.login(self.member)
        data = self.payload(
            assignee_id=self.member.id, reviewer_id=self.owner.id
        )
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["board"], self.board.id)
        self.assertEqual(response.data["assignee"]["id"], self.member.id)
        self.assertEqual(response.data["comments_count"], 0)
        task = Task.objects.get(pk=response.data["id"])
        self.assertEqual(task.created_by, self.member)

    def test_create_without_assignee_and_reviewer(self):
        self.login(self.owner)
        response = self.client.post(self.url, self.payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(response.data["assignee"])
        self.assertIsNone(response.data["reviewer"])

    def test_create_with_assignee_outside_board_fails(self):
        self.login(self.owner)
        data = self.payload(assignee_id=self.outsider.id)
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_with_invalid_status_fails(self):
        self.login(self.owner)
        data = self.payload(status="unknown")
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_with_blank_title_fails(self):
        self.login(self.owner)
        data = self.payload(title="  ")
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_without_board_fails(self):
        self.login(self.owner)
        response = self.client.post(self.url, TASK_DATA, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_on_unknown_board_returns_404(self):
        self.login(self.owner)
        data = self.payload(board=9999)
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_as_outsider_is_forbidden(self):
        self.login(self.outsider)
        response = self.client.post(self.url, self.payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_requires_authentication(self):
        response = self.client.post(self.url, self.payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TaskUpdateDeleteTests(KanbanTestCase):
    """PATCH and DELETE /api/tasks/{task_id}/"""

    def detail_url(self, task_id=None):
        return reverse("task-detail", args=[task_id or self.task.id])

    def test_member_updates_task(self):
        self.login(self.owner)
        data = {"title": "Done task", "status": "done", "assignee_id": None}
        response = self.client.patch(self.detail_url(), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "done")
        self.assertIsNone(response.data["assignee"])
        self.assertNotIn("board", response.data)
        self.assertNotIn("comments_count", response.data)

    def test_update_with_same_board_is_allowed(self):
        self.login(self.member)
        data = {"board": self.board.id, "priority": "low"}
        response = self.client.patch(self.detail_url(), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_to_other_board_fails(self):
        other = Board.objects.create(title="Other", owner=self.member)
        self.login(self.member)
        data = {"board": other.id}
        response = self.client.patch(self.detail_url(), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_with_reviewer_outside_board_fails(self):
        self.login(self.member)
        data = {"reviewer_id": self.outsider.id}
        response = self.client.patch(self.detail_url(), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_as_outsider_is_forbidden(self):
        self.login(self.outsider)
        response = self.client.patch(
            self.detail_url(), {"title": "x"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_unknown_task_returns_404(self):
        self.login(self.owner)
        response = self.client.patch(
            self.detail_url(9999), {"title": "x"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_creator_deletes_task(self):
        self.login(self.member)
        response = self.client.delete(self.detail_url())
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Task.objects.exists())

    def test_board_owner_deletes_task(self):
        self.login(self.owner)
        response = self.client.delete(self.detail_url())
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_other_member_cannot_delete_task(self):
        self.task.created_by = self.owner
        self.task.save()
        self.login(self.member)
        response = self.client.delete(self.detail_url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_task_str(self):
        self.assertEqual(str(self.task), "Task 1")


class TaskListTests(KanbanTestCase):
    """GET /api/tasks/assigned-to-me/ and /api/tasks/reviewing/"""

    def test_assigned_to_me(self):
        self.login(self.member)
        response = self.client.get(reverse("tasks-assigned-to-me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["board"], self.board.id)

    def test_reviewing(self):
        self.login(self.owner)
        response = self.client.get(reverse("tasks-reviewing"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["reviewer"]["id"], self.owner.id)

    def test_lists_are_empty_for_outsider(self):
        self.login(self.outsider)
        self.assertEqual(self.client.get(reverse("tasks-reviewing")).data, [])

    def test_lists_require_authentication(self):
        response = self.client.get(reverse("tasks-assigned-to-me"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
