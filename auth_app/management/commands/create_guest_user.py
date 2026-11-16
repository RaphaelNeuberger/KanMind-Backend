"""Management command that creates the guest account of the frontend."""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

GUEST_EMAIL = "kevin@kovacsi.de"
GUEST_PASSWORD = "asdasdasd"


class Command(BaseCommand):
    """Create (or reset) the guest user used by the frontend guest login."""

    help = "Creates the guest user for the frontend guest login."

    def handle(self, *args, **options):
        """Create the guest user if needed and reset its password."""
        user, created = get_user_model().objects.get_or_create(
            username=GUEST_EMAIL,
            defaults={"email": GUEST_EMAIL, "first_name": "Guest",
                      "last_name": "User"},
        )
        user.set_password(GUEST_PASSWORD)
        user.save()
        action = "created" if created else "updated"
        self.stdout.write(self.style.SUCCESS(f"Guest user {action}."))
