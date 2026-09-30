"""
Management command to generate a content audit report.
"""
from django.core.management.base import BaseCommand
from tourist.models import Destination, DestinationImage, DestinationVideo, Review


class Command(BaseCommand):
    help = "Generate a content audit report"

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("CONTENT AUDIT REPORT")
        self.stdout.write("=" * 60)

        # Destinations
        total_dest = Destination.objects.count()
        published = Destination.objects.filter(is_published=True).count()
        draft = Destination.objects.filter(is_published=False).count()
        featured = Destination.objects.filter(is_featured=True).count()

        self.stdout.write(f"\nDestinations:")
        self.stdout.write(f"  Total: {total_dest}")
        self.stdout.write(f"  Published: {published}")
        self.stdout.write(f"  Draft: {draft}")
        self.stdout.write(f"  Featured: {featured}")

        # Images
        total_images = DestinationImage.objects.count()
        approved = DestinationImage.objects.filter(verification_status="approved").count()
        pending = DestinationImage.objects.filter(verification_status="pending").count()
        rejected = DestinationImage.objects.filter(verification_status="rejected").count()

        self.stdout.write(f"\nImages:")
        self.stdout.write(f"  Total: {total_images}")
        self.stdout.write(f"  Approved: {approved}")
        self.stdout.write(f"  Pending: {pending}")
        self.stdout.write(f"  Rejected: {rejected}")

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
