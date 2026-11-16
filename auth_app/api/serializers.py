"""Serializers for registration, login and user representation."""

from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


def get_fullname(user):
    """Return the display name of a user (first and last name)."""
    return user.get_full_name() or user.username


class UserSerializer(serializers.ModelSerializer):
    """Read-only representation of a user: id, email and fullname."""

    fullname = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "fullname"]

    def get_fullname(self, obj):
        """Build the fullname from the user's first and last name."""
        return get_fullname(obj)


class RegistrationSerializer(serializers.ModelSerializer):
    """Validates the registration data and creates a new user."""

    fullname = serializers.CharField(max_length=150, write_only=True)
    email = serializers.EmailField(max_length=150)
    password = serializers.CharField(write_only=True)
    repeated_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["fullname", "email", "password", "repeated_password"]

    def validate_email(self, value):
        """Ensure the email address is not registered yet."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )
        return value.lower()

    def validate(self, attrs):
        """Ensure both password fields are identical."""
        if attrs["password"] != attrs["repeated_password"]:
            raise serializers.ValidationError(
                {"repeated_password": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        """Create the user; the email doubles as unique username."""
        first_name, _, last_name = validated_data["fullname"].partition(" ")
        return User.objects.create_user(
            username=validated_data["email"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=first_name,
            last_name=last_name.strip(),
        )


class LoginSerializer(serializers.Serializer):
    """Authenticates a user by email address and password."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Return the matching active user or raise a validation error."""
        user = User.objects.filter(email__iexact=attrs["email"]).first()
        if user is None or not user.is_active:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.check_password(attrs["password"]):
            raise serializers.ValidationError("Invalid email or password.")
        attrs["user"] = user
        return attrs


class EmailCheckSerializer(serializers.Serializer):
    """Validates the ``email`` query parameter of the email check."""

    email = serializers.EmailField()
