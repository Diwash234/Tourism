"""
Management command to check for outdated dependencies.
"""
import subprocess
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Check for outdated dependencies"

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("DEPENDENCY CHECK")
        self.stdout.write("=" * 60)

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
                self.stdout.write("All Python dependencies are up to date")
        except Exception as exc:
            self.stderr.write(f"Error checking Python dependencies: {exc}")

        # Check Node.js dependencies
        self.stdout.write("\nNode.js Dependencies:")
        frontend_dir = Path("frontend/Tourism")
        if (frontend_dir / "package.json").exists():
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
                    self.stdout.write("All Node.js dependencies are up to date")
            except Exception as exc:
                self.stderr.write(f"Error checking Node.js dependencies: {exc}")
        else:
            self.stdout.write("No package.json found")

        self.stdout.write("\n" + "=" * 60)
