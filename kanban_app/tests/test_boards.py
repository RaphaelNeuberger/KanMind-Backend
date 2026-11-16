"""Tests for the board endpoints."""

from django.urls import reverse
from rest_framework import status

from kanban_app.models import Board, Task

from .helpers import KanbanTestCase


class BoardListCreateTests(KanbanTestCase):
    """GET and POST /api/boards/"""

    url = reverse("board-list")

    def test_list_requires_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_returns_boards_with_counters(self):
        self.login(self.member)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [{
            "id": self.board.id, "title": "Project X", "member_count": 2,
            "ticket_count": 1, "tasks_to_do_count": 1,
            "tasks_high_prio_count": 1, "owner_id": self.owner.id,
        }])

    def test_list_hides_foreign_boards(self):
        self.login(self.outsider)
        response = self.client.get(self.url)
        self.assertEqual(response.data, [])

    def test_create_board_adds_owner_as_member(self):
        self.login(self.outsider)
        data = {"title": "New", "members": [self.member.id]}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["owner_id"], self.outsider.id)
        self.assertEqual(response.data["member_count"], 2)
        self.assertNotIn("members", response.data)

    def test_create_board_with_invalid_member_fails(self):
        self.login(self.owner)
        data = {"title": "New", "members": [9999]}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_board_with_blank_title_fails(self):
        self.login(self.owner)
        response = self.client.post(self.url, {"title": " "}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class BoardDetailTests(KanbanTestCase):
    """GET, PATCH and DELETE /api/boards/{board_id}/"""

    def detail_url(self, board_id=None):
        return reverse("board-detail", args=[board_id or self.board.id])

    def test_retrieve_board_with_members_and_tasks(self):
        self.login(self.member)
        response = self.client.get(self.detail_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["owner_id"], self.owner.id)
        self.assertEqual(len(response.data["members"]), 2)
        task = response.data["tasks"][0]
        self.assertEqual(task["comments_count"], 1)
        self.assertEqual(task["assignee"]["email"], "member@example.com")
        self.assertNotIn("board", task)

    def test_retrieve_without_trailing_slash(self):
        self.login(self.member)
        response = self.client.get(f"/api/boards/{self.board.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_as_outsider_is_forbidden(self):
        self.login(self.outsider)
        response = self.client.get(self.detail_url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_unknown_board_returns_404(self):
        self.login(self.owner)
        response = self.client.get(self.detail_url(9999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_member_can_update_title_and_members(self):
        self.login(self.member)
        data = {"title": "Changed", "members": [self.outsider.id]}
        response = self.client.patch(self.detail_url(), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Changed")
        self.assertEqual(response.data["owner_data"]["id"], self.owner.id)
        member_ids = {m["id"] for m in response.data["members_data"]}
        self.assertEqual(member_ids, {self.owner.id, self.outsider.id})

    def test_update_title_only_keeps_members(self):
        self.login(self.owner)
        response = self.client.patch(
            self.detail_url(), {"title": "Only title"}, format="json"
        )
        self.assertEqual(len(response.data["members_data"]), 2)

    def test_update_as_outsider_is_forbidden(self):
        self.login(self.outsider)
        response = self.client.patch(
            self.detail_url(), {"title": "Hack"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_with_invalid_member_fails(self):
        self.login(self.owner)
        response = self.client.patch(
            self.detail_url(), {"members": [9999]}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_is_not_allowed(self):
        self.login(self.owner)
        response = self.client.put(
            self.detail_url(), {"title": "x"}, format="json"
        )
        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_owner_can_delete_board_with_tasks(self):
        self.login(self.owner)
        response = self.client.delete(self.detail_url())
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Board.objects.exists())
        self.assertFalse(Task.objects.exists())

    def test_member_cannot_delete_board(self):
        self.login(self.member)
        response = self.client.delete(self.detail_url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_board_str(self):
        self.assertEqual(str(self.board), "Project X")
