"""Serializers for boards, tasks and comments."""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from auth_app.api.serializers import UserSerializer, get_fullname
from kanban_app.models import Board, Comment, Task

from .permissions import is_board_member

User = get_user_model()


class BoardTaskSerializer(serializers.ModelSerializer):
    """Read representation of a task inside the board detail view."""

    assignee = UserSerializer(read_only=True)
    reviewer = UserSerializer(read_only=True)
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id", "title", "description", "status", "priority",
            "assignee", "reviewer", "due_date", "comments_count",
        ]

    def get_comments_count(self, obj):
        """Return the number of comments of the task."""
        return obj.comments.count()


class TaskSerializer(BoardTaskSerializer):
    """Read representation of a task including its board id."""

    class Meta(BoardTaskSerializer.Meta):
        fields = ["id", "board"] + BoardTaskSerializer.Meta.fields[1:]


class TaskCreateSerializer(TaskSerializer):
    """Creates a task; assignee and reviewer are passed as user ids."""

    assignee_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="assignee",
        write_only=True, required=False, allow_null=True,
    )
    reviewer_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="reviewer",
        write_only=True, required=False, allow_null=True,
    )

    class Meta(TaskSerializer.Meta):
        fields = TaskSerializer.Meta.fields + ["assignee_id", "reviewer_id"]

    def validate(self, attrs):
        """Ensure assignee and reviewer are members of the task's board."""
        board = attrs.get("board") or self.instance.board
        for field in ("assignee", "reviewer"):
            user = attrs.get(field)
            if user is not None and not is_board_member(user, board):
                raise serializers.ValidationError(
                    {f"{field}_id": "User must be a member of the board."}
                )
        return attrs


class TaskUpdateSerializer(TaskCreateSerializer):
    """Partially updates a task; moving it to another board is forbidden."""

    class Meta(TaskCreateSerializer.Meta):
        fields = [
            "id", "board", "title", "description", "status", "priority",
            "assignee", "reviewer", "assignee_id", "reviewer_id", "due_date",
        ]
        extra_kwargs = {"board": {"write_only": True}}

    def validate_board(self, value):
        """Only allow the board the task already belongs to."""
        if value != self.instance.board:
            raise serializers.ValidationError(
                "The board of a task cannot be changed."
            )
        return value


class BoardListSerializer(serializers.ModelSerializer):
    """Board overview with counters; also used to create a board."""

    members = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), many=True,
        write_only=True, required=False,
    )
    member_count = serializers.SerializerMethodField()
    ticket_count = serializers.SerializerMethodField()
    tasks_to_do_count = serializers.SerializerMethodField()
    tasks_high_prio_count = serializers.SerializerMethodField()
    owner_id = serializers.ReadOnlyField(source="owner.id")

    class Meta:
        model = Board
        fields = [
            "id", "title", "members", "member_count", "ticket_count",
            "tasks_to_do_count", "tasks_high_prio_count", "owner_id",
        ]

    def get_member_count(self, obj):
        """Return the number of board members."""
        return obj.members.count()

    def get_ticket_count(self, obj):
        """Return the number of tasks on the board."""
        return obj.tasks.count()

    def get_tasks_to_do_count(self, obj):
        """Return the number of tasks with status 'to-do'."""
        return obj.tasks.filter(status=Task.Status.TO_DO).count()

    def get_tasks_high_prio_count(self, obj):
        """Return the number of tasks with priority 'high'."""
        return obj.tasks.filter(priority=Task.Priority.HIGH).count()

    def create(self, validated_data):
        """Create the board with exactly the given members."""
        members = validated_data.pop("members", [])
        board = Board.objects.create(**validated_data)
        board.members.set(members)
        return board


class BoardDetailSerializer(serializers.ModelSerializer):
    """Board detail with its members and tasks."""

    owner_id = serializers.ReadOnlyField(source="owner.id")
    members = UserSerializer(many=True, read_only=True)
    tasks = BoardTaskSerializer(many=True, read_only=True)

    class Meta:
        model = Board
        fields = ["id", "title", "owner_id", "members", "tasks"]


class BoardUpdateSerializer(serializers.ModelSerializer):
    """Updates title and the complete member list of a board."""

    members = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), many=True,
        write_only=True, required=False,
    )
    owner_data = UserSerializer(source="owner", read_only=True)
    members_data = UserSerializer(source="members", many=True, read_only=True)

    class Meta:
        model = Board
        fields = ["id", "title", "members", "owner_data", "members_data"]

    def update(self, instance, validated_data):
        """Replace the complete member list if one is sent."""
        members = validated_data.pop("members", None)
        instance = super().update(instance, validated_data)
        if members is not None:
            instance.members.set(members)
        return instance


class CommentSerializer(serializers.ModelSerializer):
    """Comment with creation date, author name and content."""

    author = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ["id", "created_at", "author", "content"]
        read_only_fields = ["id", "created_at"]

    def get_author(self, obj):
        """Return the fullname of the comment author."""
        return get_fullname(obj.author)
