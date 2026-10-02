"""
Management command to rotate API keys and secrets.
"""
import secrets
import string
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate new secrets for API keys and tokens"

    def add_arguments(self, parser):
        parser.add_argument(
            "--length",
            type=int,
            default=64,
            help="Length of the generated secret",
        )

    def handle(self, *args, **options):
        length = options["length"]

        # Generate a secure random secret
        alphabet = string.ascii_letters + string.digits + string.punctuation
        secret = "".join(secrets.choice(alphabet) for _ in range(length))

        self.stdout.write("=" * 60)
        self.stdout.write("GENERATED SECRET (store securely!)")
        self.stdout.write("=" * 60)
        self.stdout.write(secret)
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.WARNING("Store this secret in your environment variables."))
        self.stdout.write(self.style.WARNING("Do not commit it to version control!"))
