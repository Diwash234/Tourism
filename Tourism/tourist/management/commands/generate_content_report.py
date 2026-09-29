"""
Management command to generate a content report.
"""
from django.core.management.base import BaseCommand
from tourist.models import Destination, DestinationImage, DestinationVideo, Review


class Command(BaseCommand):
    help = "Generate a content report"

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("CONTENT REPORT")
        self.stdout.write("=" * 60)

        # Destinations
        total_dest = Destination.objects.count()
        published = Destination.objects.filter(is_published=True).count()
        draft = Destination.objects.filter(is_published=False).count()
        self.stdout.write(f"\nDestinations:")
        self.stdout.write(f"  Total: {total_dest}")
        self.stdout.write(f"  Published: {published}")
        self.stdout.write(f"  Draft: {draft}")

        # Images
        total_images = DestinationImage.objects.count()
        approved = DestinationImage.objects.filter(verification_status="approved").count()
        pending = DestinationImage.objects.filter(verification_status="pending").count()
        self.stdout.write(f"\nImages:")
        self.stdout.write(f"  Total: {total_images}")
        self.stdout.write(f"  Approved: {approved}")
        self.stdout.write(f"  Pending: {pending}")

        # Videos
        total_videos = DestinationVideo.objects.count()
        self.stdout.write(f"\nVideos: {total_videos}")

        # Reviews
        total_reviews = Review.objects.count()
        approved_reviews = Review.objects.filter(is_approved=True).count()
        pending_reviews = Review.objects.filter(is_approved=False).count()
        self.stdout.write(f"\nReviews:")
        self.stdout.write(f"  Total: {total_reviews}")
        self.stdout.write(f"  Approved: {approved_reviews}")
        self.stdout.write(f"  Pending: {pending_reviews}")

        self.stdout.write("\n" + "=" * 60)
