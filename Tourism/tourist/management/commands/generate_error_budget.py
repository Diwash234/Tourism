"""
Management command to generate an error budget configuration.
"""
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate an error budget configuration"

    def handle(self, *args, **options):
        self.stdout.write("Generating error budget configuration...")

        content = """# Error Budget Configuration
error_budget:
  slo: 99.9
  window: 30d
  budget: 0.1

alerts:
  - name: "Error Budget Burn Rate"
    condition: "burn_rate > 2"
    severity: warning
  - name: "Error Budget Exhausted"
    condition: "budget_remaining < 0"
    severity: critical
"""

        with open(Path("error_budget.yml"), "w") as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS("Error budget configuration generated at error_budget.yml"))
