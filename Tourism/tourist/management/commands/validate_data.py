"""
Management command to validate data integrity.
"""
from django.core.management.base import BaseCommand
from django.db.models import Q, Count
from tourist.models import Destination, DestinationImage, Category, Review


class Command(BaseCommand):
    help = "Validate data integrity across all models"

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("DATA INTEGRITY VALIDATION REPORT")
        self.stdout.write("=" * 60)

        issues = []

        # Check for orphaned destinations (no category)
        orphaned = Destination.objects.filter(category__isnull=True).count()
        if orphaned:
            issues.append(f"  [WARNING] {orphaned} destinations without a category")
        else:
            self.stdout.write(self.style.SUCCESS("  [OK] All destinations have categories"))

        # Check for duplicate slugs
        dup_slugs = Destination.objects.values("slug").annotate(
            count=Count("id")
        ).filter(count__gt=1)
        if dup_slugs:
            issues.append(f"  [ERROR] {len(dup_slugs)} duplicate slugs found")
            for d in dup_slugs:
                issues.append(f"    - {d['slug']}: {d['count']} occurrences")
        else:
            self.stdout.write(self.style.SUCCESS("  [OK] No duplicate slugs"))

        # Check for invalid coordinates
        invalid_coords = Destination.objects.filter(
            Q(latitude__isnull=True) | Q(longitude__isnull=True) |
            Q(latitude__lt=-90) | Q(latitude__gt=90) |
            Q(longitude__lt=-180) | Q(longitude__gt=180)
        ).count()
        if invalid_coords:
            issues.append(f"  [WARNING] {invalid_coords} destinations with invalid coordinates")
        else:
            self.stdout.write(self.style.SUCCESS("  [OK] All coordinates are valid"))

        # Check for broken image references
        broken_images = DestinationImage.objects.filter(
            Q(image_path__isnull=True) | Q(image_path="")
        ).count()
        if broken_images:
            issues.append(f"  [WARNING] {broken_images} images with missing paths")
        else:
            self.stdout.write(self.style.SUCCESS("  [OK] All image paths are valid"))

        # Check for unpublished destinations with published images.
        # The model has no `is_published` field - public visibility is
        # `is_active` plus the approval `status` - so this check used to raise
        # FieldError every time the command ran.
        unpublished_with_images = Destination.objects.filter(
            Q(is_active=False) | ~Q(status=Destination.SubmissionStatus.APPROVED),
            gallery__verification_status="approved",
        ).distinct().count()
        if unpublished_with_images:
            issues.append(f"  [INFO] {unpublished_with_images} unpublished destinations have approved images")

        # Summary
        self.stdout.write("\n" + "=" * 60)
        if issues:
            self.stdout.write(self.style.WARNING(f"Found {len(issues)} issue(s):"))
            for issue in issues:
                self.stdout.write(issue)
        else:
            self.stdout.write(self.style.SUCCESS("All data integrity checks passed!"))
        self.stdout.write("=" * 60)
