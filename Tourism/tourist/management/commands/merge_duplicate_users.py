"""
Management command to merge duplicate user accounts.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from tourist.models import User, TravelPlan, Review, Favorite


class Command(BaseCommand):
    help = "Merge duplicate user accounts"

    def add_arguments(self, parser):
        parser.add_argument(
            "--keep",
            type=int,
            required=True,
            help="User ID to keep",
        )
        parser.add_argument(
            "--merge",
            type=int,
            required=True,
            help="User ID to merge into the kept user",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be merged without making changes",
        )

    def handle(self, *args, **options):
        keep_id = options["keep"]
        merge_id = options["merge"]
        dry_run = options["dry_run"]

        try:
            keep_user = User.objects.get(id=keep_id)
            merge_user = User.objects.get(id=merge_id)
        except User.DoesNotExist:
            self.stderr.write("One or both users not found")
            return

        self.stdout.write(f"Keeping user: {keep_user.email} (ID: {keep_id})")
        self.stdout.write(f"Merging user: {merge_user.email} (ID: {merge_id})")

        # Count related objects
        plans = TravelPlan.objects.filter(user=merge_user).count()
        reviews = Review.objects.filter(user=merge_user).count()
        favorites = Favorite.objects.filter(user=merge_user).count()

        self.stdout.write(f"  Travel plans to merge: {plans}")
        self.stdout.write(f"  Reviews to merge: {reviews}")
        self.stdout.write(f"  Favorites to merge: {favorites}")

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run — no changes made"))
            return

        with transaction.atomic():
            # Transfer related objects
            TravelPlan.objects.filter(user=merge_user).update(user=keep_user)
            Review.objects.filter(user=merge_user).update(user=keep_user)
            Favorite.objects.filter(user=merge_user).update(user=keep_user)

            # Delete the merged user
            merge_user.delete()

        self.stdout.write(self.style.SUCCESS("Users merged successfully"))
