"""Object-level permissions for boards, tasks and comments."""

from rest_framework.permissions import BasePermission

from kanban_app.models import Board


def get_board(obj):
    """Return the board itself or the board a task belongs to."""
    if isinstance(obj, Board):
        return obj
    return obj.board


def is_board_member(user, board):
    """Return True if the user owns the board or is one of its members."""
    if board.owner_id == user.id:
        return True
    return board.members.filter(pk=user.pk).exists()


class IsBoardMemberOrOwner(BasePermission):
    """Grants access to the owner and the members of the related board."""

    message = "You must be a member or the owner of this board."

    def has_object_permission(self, request, view, obj):
        """Check membership on the board the object belongs to."""
        return is_board_member(request.user, get_board(obj))


class IsBoardOwner(BasePermission):
    """Grants access only to the owner of the related board."""

    message = "Only the owner of this board may do this."

    def has_object_permission(self, request, view, obj):
        """Compare the board owner with the requesting user."""
        return get_board(obj).owner_id == request.user.id


class IsTaskCreatorOrBoardOwner(BasePermission):
    """Grants access to the creator of a task or the owner of its board."""

    message = "Only the task creator or the board owner may delete a task."

    def has_object_permission(self, request, view, obj):
        """Check whether the user created the task or owns the board."""
        user_id = request.user.id
        return obj.created_by_id == user_id or obj.board.owner_id == user_id


class IsCommentAuthor(BasePermission):
    """Grants access only to the author of a comment."""

    message = "Only the author of this comment may delete it."

    def has_object_permission(self, request, view, obj):
        """Compare the comment author with the requesting user."""
        return obj.author_id == request.user.id
