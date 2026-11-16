"""API views for registration, login and the email check."""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    EmailCheckSerializer,
    LoginSerializer,
    RegistrationSerializer,
    UserSerializer,
    get_fullname,
)

User = get_user_model()


def build_auth_response(user):
    """Return the token and user data the frontend expects after auth."""
    token, _ = Token.objects.get_or_create(user=user)
    return {
        "token": token.key,
        "fullname": get_fullname(user),
        "email": user.email,
        "user_id": user.id,
    }


class RegistrationView(APIView):
    """POST /api/registration/ - create a new user account."""

    permission_classes = [AllowAny]

    def post(self, request):
        """Validate the data, create the user and return its token."""
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            build_auth_response(user), status=status.HTTP_201_CREATED
        )


class LoginView(APIView):
    """POST /api/login/ - log in with email and password."""

    permission_classes = [AllowAny]

    def post(self, request):
        """Check the credentials and return the user's token."""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        return Response(build_auth_response(user), status=status.HTTP_200_OK)


class EmailCheckView(APIView):
    """GET /api/email-check/?email=... - look up a user by email."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return the user with the given email or 404 if none exists."""
        serializer = EmailCheckSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        user = User.objects.filter(email__iexact=email).first()
        if user is None:
            raise NotFound("No user with this email address exists.")
        return Response(UserSerializer(user).data)
