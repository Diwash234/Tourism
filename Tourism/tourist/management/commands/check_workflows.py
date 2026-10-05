"""Validate the GitHub Actions workflows in this repository.

Two things go wrong with workflow files, and neither shows up until the workflow
is dispatched:

  * the YAML is malformed, or contains a duplicate key, and the run fails before
    doing anything;
  * the YAML is fine but calls a management command that does not exist, so the
    job fails at the first step.

Both are cheap to catch here and expensive to discover on a production
dispatch. Duplicate keys in particular are silent in most YAML readers -- the
second one just wins -- so they are checked explicitly.

Usage:
    python manage.py check_workflows
"""
from __future__ import annotations

import re
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


class _StrictLoader(yaml.SafeLoader if yaml else object):
    """Refuses duplicate mapping keys instead of silently taking the last one."""


if yaml:
    def _no_duplicates(loader, node, deep=False):
        mapping = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            if key in mapping:
                raise yaml.constructor.ConstructorError(
                    "while constructing a mapping", node.start_mark,
                    f"found duplicate key {key!r}", key_node.start_mark,
                )
            mapping[key] = loader.construct_object(value_node, deep=deep)
        return mapping

    _StrictLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _no_duplicates
    )


# `manage.py <name>` inside a run: block, possibly with line continuations.
_COMMAND = re.compile(r"manage\.py\s+([a-z0-9_]+)")

IGNORED_COMMANDS = {
    "migrate", "makemigrations", "check", "test", "collectstatic", "shell",
    "createsuperuser", "showmigrations", "flush", "dumpdata", "loaddata",
    "compilemessages", "makemessages", "diffsettings", "inspectdb", "sqmigrate",
    "dbshell", "shell_plus", "runserver", "waitress-serve",
}


class Command(BaseCommand):
    help = "Validate .github/workflows/*.yml: YAML shape and referenced commands."

    def add_arguments(self, parser):
        parser.add_argument("--dir", default="", help="Workflow directory override.")

    def handle(self, *args, **options):
        root = Path(options["dir"]) if options["dir"] else Path(settings.BASE_DIR).parent
        workflow_dir = root / ".github" / "workflows"
        # Every failure path exits non-zero. A checker that prints ERROR and
        # returns 0 is worse than no checker, because CI reports success.
        if not workflow_dir.exists():
            self.stdout.write(self.style.ERROR(f"no workflow directory at {workflow_dir}"))
            raise SystemExit(1)

        files = sorted(list(workflow_dir.glob("*.yml")) + list(workflow_dir.glob("*.yaml")))
        if not files:
            self.stdout.write(self.style.ERROR(f"no workflow files in {workflow_dir}"))
            raise SystemExit(1)

        available = self._available_commands()
        failures = 0

        for path in files:
            self.stdout.write(f"\n{path.name}")
            text = path.read_text(encoding="utf-8")
            try:
                document = yaml.load(text, Loader=_StrictLoader)  # noqa: S506
            except yaml.YAMLError as exc:
                self.stdout.write(self.style.ERROR(f"  YAML INVALID: {exc}"))
                failures += 1
                continue
            self.stdout.write("  YAML valid (no duplicate keys)")

            if not isinstance(document, dict) or "jobs" not in document:
                self.stdout.write(self.style.ERROR("  no 'jobs' key"))
                failures += 1
                continue

            referenced = sorted({m for m in _COMMAND.findall(text)} - IGNORED_COMMANDS)
            if not referenced:
                self.stdout.write("  no custom management commands referenced")
            for command in referenced:
                if command in available:
                    self.stdout.write(f"  manage.py {command}: found")
                else:
                    self.stdout.write(self.style.ERROR(
                        f"  manage.py {command}: MISSING -- this workflow cannot work"
                    ))
                    failures += 1

            # Per job, not per file. Checking the file text would let one job's
            # timeout excuse every other job in the same workflow, which is
            # exactly the kind of false assurance this command exists to remove.
            jobs = document.get("jobs") or {}
            for job_name, job in jobs.items():
                if not isinstance(job, dict):
                    self.stdout.write(self.style.ERROR(f"  job {job_name}: not a mapping"))
                    failures += 1
                    continue
                if "timeout-minutes" not in job:
                    self.stdout.write(self.style.WARNING(
                        f"  job {job_name}: no timeout-minutes; a hung step runs to "
                        "the 6h GitHub job limit"
                    ))

        self.stdout.write("")
        if failures:
            self.stdout.write(self.style.ERROR(f"{failures} problem(s) found"))
            raise SystemExit(1)
        self.stdout.write(self.style.SUCCESS(f"all {len(files)} workflow(s) valid"))

    def _available_commands(self) -> set[str]:
        commands_dir = Path(settings.BASE_DIR) / "tourist" / "management" / "commands"
        if not commands_dir.exists():
            return set()
        return {p.stem for p in commands_dir.glob("*.py") if p.stem != "__init__"}
