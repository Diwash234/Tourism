"""
Management command to clear the cache.
"""
from django.core.management.base import BaseCommand
from django.core.cache import cache


class Command(BaseCommand):
    help = "Clear the application cache"

    def add_arguments(self, parser):
        parser.add_argument(
            "--pattern",
            type=str,
            default="",
            help="Clear only keys matching this pattern",
        )

    def handle(self, *args, **options):
        pattern = options["pattern"]

        if pattern:
            self.stdout.write(f"Clearing cache keys matching '{pattern}'...")
            # This requires Redis backend
            try:
                from django_redis import get_redis_connection
                redis = get_redis_connection("default")
                keys = redis.keys(f"*{pattern}*")
                if keys:
                    redis.delete(*keys)
                    self.stdout.write(self.style.SUCCESS(f"Cleared {len(keys)} cache keys"))
                else:
                    self.stdout.write("No matching cache keys found")
            except Exception as exc:
                self.stderr.write(f"Error: {exc}")
        else:
            self.stdout.write("Clearing entire cache...")
            cache.clear()
            self.stdout.write(self.style.SUCCESS("Cache cleared successfully"))
