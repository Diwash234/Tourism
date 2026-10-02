"""
Management command to generate SEO recommendations.
"""
from django.core.management.base import BaseCommand
from tourist.models import Destination


class Command(BaseCommand):
    help = "Generate SEO recommendations"

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("SEO RECOMMENDATIONS")
        self.stdout.write("=" * 60)

        # Check for missing meta descriptions
        no_desc = Destination.objects.filter(
            is_published=True,
            description__isnull=True,
        ).count()
        self.stdout.write(f"\nDestinations without description: {no_desc}")
        if no_desc > 0:
            self.stdout.write("  → Add unique meta descriptions to improve search visibility")

        # Check for short descriptions
        short_desc = Destination.objects.filter(
            is_published=True,
            description__length__lt=50,
        ).count()
        self.stdout.write(f"Destinations with short descriptions: {short_desc}")
        if short_desc > 0:
            self.stdout.write("  → Expand descriptions to 150-160 characters for better SEO")

        # Check for missing slugs
        no_slug = Destination.objects.filter(
            is_published=True,
            slug__isnull=True,
        ).count()
        self.stdout.write(f"Destinations without slug: {no_slug}")
        if no_slug > 0:
            self.stdout.write("  → Add SEO-friendly slugs to all destinations")

        # Check for duplicate names
        dup_names = Destination.objects.values("name").annotate(
            count=models.Count("id")
        ).filter(count__gt=1)
        self.stdout.write(f"Duplicate destination names: {dup_names.count()}")
        if dup_names.count() > 0:
            self.stdout.write("  → Consider merging or differentiating duplicate destinations")

        # Recommendations
        self.stdout.write("\nGeneral SEO Recommendations:")
        self.stdout.write("  1. Add structured data (Schema.org) to destination pages")
        self.stdout.write("  2. Implement canonical URLs to avoid duplicate content")
        self.stdout.write("  3. Add Open Graph tags for social media sharing")
        self.stdout.write("  4. Implement hreflang tags for multi-language support")
        self.stdout.write("  5. Add XML sitemap and submit to Google Search Console")
        self.stdout.write("  6. Optimize images with alt tags and descriptive filenames")
        self.stdout.write("  7. Implement lazy loading for images")
        self.stdout.write("  8. Add breadcrumb navigation for better UX and SEO")

        self.stdout.write("\n" + "=" * 60)
