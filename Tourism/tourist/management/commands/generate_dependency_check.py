"""
Management command to check for outdated dependencies.
"""
import subprocess
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Check for outdated dependencies"

    def handle(self, *args, **options):
        self.stdout.write("Checking for outdated dependencies...")

        # Check Python dependencies
        self.stdout.write("\nPython Dependencies:")
        try:
            result = subprocess.run(
                ["pip", "list", "--outdated", "--format=columns"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.stdout:
                self.stdout.write(result.stdout)
            else:
                self.stdout.write(self.style.SUCCESS("  All Python dependencies are up to date"))
        except Exception as exc:
            self.stderr.write(f"  Error checking Python dependencies: {exc}")

        # Check Node.js dependencies
        self.stdout.write("\nNode.js Dependencies:")
        frontend_dir = "frontend/Tourism"
        try:
            result = subprocess.run(
                ["npm", "outdated"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=frontend_dir,
            )
            if result.stdout:
                self.stdout.write(result.stdout)
            else:
                self.stdout.write(self.style.SUCCESS("  All Node.js dependencies are up to date"))
        except Exception as exc:
            self.stderr.write(f"  Error checking Node.js dependencies: {exc}")

        self.stdout.write(self.style.SUCCESS("\nDependency check completed"))
