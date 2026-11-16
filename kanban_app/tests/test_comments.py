"""Tests for the comment endpoints."""

from django.urls import reverse
from rest_framework import status

from kanban_app.models import Comment

from .helpers import KanbanTestCase


class CommentTests(KanbanTestCase):
    """GET, POST and DELETE /api/tasks/{task_id}/comments/"""

    def list_url(self, task_id=None):
        return reverse("task-comments", args=[task_id or self.task.id])

    def detail_url(self, comment_id=None, task_id=None):
        return reverse(
            "task-comment-detail",
            args=[task_id or self.task.id, comment_id or self.comment.id],
        )

    def test_member_lists_comments(self):
        self.login(self.owner)
        response = self.client.get(self.list_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            set(response.data[0]), {"id", "created_at", "author", "content"}
        )
        self.assertEqual(response.data[0]["author"], "Member Tester")

    def test_outsider_cannot_list_comments(self):
        self.login(self.outsider)
        response = self.client.get(self.list_url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_comments_of_unknown_task_return_404(self):
        self.login(self.owner)
        response = self.client.get(self.list_url(9999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_member_creates_comment(self):
        self.login(self.owner)
        data = {"content": "New comment"}
        response = self.client.post(self.list_url(), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["author"], "Owner Tester")
        self.assertEqual(self.task.comments.count(), 2)

    def test_create_blank_comment_fails(self):
        self.login(self.owner)
        response = self.client.post(
            self.list_url(), {"content": "  "}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_outsider_cannot_create_comment(self):
        self.login(self.outsider)
        response = self.client.post(
            self.list_url(), {"content": "Hi"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_author_deletes_comment(self):
        self.login(self.member)
        response = self.client.delete(self.detail_url())
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Comment.objects.exists())

    def test_other_member_cannot_delete_comment(self):
        self.login(self.owner)
        response = self.client.delete(self.detail_url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_unknown_comment_returns_404(self):
        self.login(self.member)
        response = self.client.delete(self.detail_url(comment_id=9999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_comment_str(self):
        self.assertIn("First comment", str(self.comment))
