from django.core.management.base import BaseCommand

from tourist.notification_delivery import process_due_notifications


class Command(BaseCommand):
    help = "Deliver queued email, SMS and push notifications with bounded retries."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=100)

    def handle(self, *args, **options):
        limit = max(1, min(options["limit"], 1000))
        result = process_due_notifications(limit=limit)
        self.stdout.write(self.style.SUCCESS(
            f"Processed {result['processed']}; sent {result.get('sent', 0)}; failed {result.get('failed', 0)}"
        ))
