"""
Management command to export user data for GDPR compliance.
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand
from tourist.models import User, TravelPlan, Review, Favorite


class Command(BaseCommand):
    help = "Export all data for a specific user (GDPR data portability)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--user-id",
            type=int,
            required=True,
            help="User ID to export data for",
        )
        parser.add_argument(
            "--output",
            type=str,
            default="user_data_export.json",
            help="Output file path",
        )

    def handle(self, *args, **options):
        user_id = options["user_id"]
        output_file = Path(options["output"])

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            self.stderr.write(f"User {user_id} not found")
            return

        self.stdout.write(f"Exporting data for user {user_id}...")

        # Collect all user data
        data = {
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "date_joined": user.date_joined.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None,
            },
            "travel_plans": list(TravelPlan.objects.filter(user=user).values()),
            "reviews": list(Review.objects.filter(user=user).values()),
            "favorites": list(Favorite.objects.filter(user=user).values()),
        }

        with open(output_file, "w") as f:
            json.dump(data, f, indent=2, default=str)

        self.stdout.write(self.style.SUCCESS(f"User data exported to {output_file}"))
