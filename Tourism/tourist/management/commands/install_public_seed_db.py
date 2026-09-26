"""Install the published public seed database into a fresh clone.

Why this exists
---------------
A new clone receives the code, not the operational database. This command
installs the published, privacy-safe seed database so a collaborator has real
tourism content on the first run:

    python manage.py install_public_seed_db

The seed database is the same public artifact that CI checksums. It contains
destinations, galleries, hotels, hospitals, police stations, restaurants, OSM
services, transit routes and published CMS pages. It never contains accounts,
password hashes, tokens, sessions, chats, bookings, notifications, audit logs,
drafts or local media paths, so it is safe to keep in a public repository.

This command never overwrites real work: it refuses to touch a database that
already has users or destinations unless --force is given, and it always
verifies the archive checksum, SQLite integrity, and foreign keys first.
"""
from __future__ import annotations

import gzip
import hashlib
import os
import shutil
import sqlite3
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

ARCHIVE_NAME = "nepal-tourism-seed.sqlite3.gz"
SIDECAR_SUFFIX = ".sha256"

# Content the friend can expect, used only for reporting and a sanity floor.
EXPECTED_MINIMUMS = {
    "tourist_destination": 1000,
    "tourist_destinationimage": 1000,
    "tourist_managedpage": 1,
}

# Tables that must be empty in any published seed database.
MUST_BE_EMPTY = (
    "tourist_user",
    "audit_auditlog",
    "audit_errorevent",
    "django_session",
    "token_blacklist_outstandingtoken",
    "tourist_notification",
)


def archive_path() -> Path:
    return Path(settings.BASE_DIR).parent / "downloads" / ARCHIVE_NAME


def sidecar_path() -> Path:
    return archive_path().with_suffix(archive_path().suffix + SIDECAR_SUFFIX)


def database_path() -> Path:
    configured = connection.settings_dict.get("NAME") or ""
    return Path(configured)


class Command(BaseCommand):
    help = "Install the published privacy-safe seed database into this clone."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help=(
                "Replace the local database even if it already contains users "
                "or destinations. The existing file is backed up first."
            ),
        )
        parser.add_argument(
            "--verify-only",
            action="store_true",
            help="Check the archive and report its contents without installing.",
        )
        parser.add_argument(
            "--skip-checksum",
            action="store_true",
            help="Skip the SHA-256 sidecar check (not recommended).",
        )

    def handle(self, *args, **options):
        archive = archive_path()
        if not archive.exists():
            raise CommandError(
                f"Seed archive not found: {archive}\n"
                "Run `git pull` first; the archive is tracked in downloads/."
            )

        if not options["skip_checksum"]:
            self._verify_checksum(archive)

        extracted = self._extract(archive)
        try:
            self._verify_database(extracted, verify_only=options["verify_only"])
            if options["verify_only"]:
                return
            target = self._install(extracted, force=options["force"])
        finally:
            try:
                extracted.unlink(missing_ok=True)
            except OSError:
                pass

        self._report(target)

    # -- steps ---------------------------------------------------------------

    def _verify_checksum(self, archive: Path) -> None:
        sidecar = sidecar_path()
        if not sidecar.exists():
            raise CommandError(f"Checksum sidecar missing: {sidecar}")
        expected = sidecar.read_text(encoding="utf-8").split()[0].strip().lower()
        actual = hashlib.sha256(archive.read_bytes()).hexdigest()
        if actual != expected:
            raise CommandError(
                f"Checksum mismatch for {archive.name}:\n"
                f"  expected {expected}\n  actual   {actual}\n"
                "The archive is corrupt or was modified. Re-run `git pull`."
            )
        self.stdout.write(f"checksum ok: {actual[:16]}...")

    def _extract(self, archive: Path) -> Path:
        handle = tempfile.NamedTemporaryFile(
            prefix="nepal-yatra-seed-", suffix=".sqlite3", delete=False
        )
        handle.close()
        destination = Path(handle.name)
        try:
            with gzip.open(archive, "rb") as source:
                with destination.open("wb") as target:
                    shutil.copyfileobj(source, target)
        except OSError as exc:
            destination.unlink(missing_ok=True)
            raise CommandError(f"Could not decompress {archive.name}: {exc}") from exc
        return destination

    def _verify_database(self, path: Path, verify_only: bool = False) -> None:
        connection_data = sqlite3.connect(path)
        try:
            integrity = connection_data.execute("pragma integrity_check").fetchone()[0]
            if integrity != "ok":
                raise CommandError(f"Seed database failed integrity check: {integrity}")

            violations = connection_data.execute("pragma foreign_key_check").fetchall()
            if violations:
                raise CommandError(
                    f"Seed database has {len(violations)} foreign key violations, "
                    f"first: {violations[0]}"
                )

            for table in MUST_BE_EMPTY:
                try:
                    count = connection_data.execute(
                        f'select count(*) from "{table}"'
                    ).fetchone()[0]
                except sqlite3.OperationalError:
                    continue
                if count:
                    raise CommandError(
                        f"Refusing to install: published seed database contains "
                        f"{count} rows in {table}."
                    )

            counts = {}
            for table, minimum in EXPECTED_MINIMUMS.items():
                try:
                    counts[table] = connection_data.execute(
                        f'select count(*) from "{table}"'
                    ).fetchone()[0]
                except sqlite3.OperationalError as exc:
                    raise CommandError(f"Seed database is missing {table}") from exc
                if counts[table] < minimum:
                    raise CommandError(
                        f"Seed database looks truncated: {table} has "
                        f"{counts[table]} rows, expected at least {minimum}."
                    )
            self._counts = counts
        finally:
            connection_data.close()

        if verify_only:
            self.stdout.write("verification only; nothing was installed")
            for table, count in self._counts.items():
                self.stdout.write(f"  {table}: {count}")

    def _install(self, extracted: Path, force: bool) -> Path:
        target = database_path()
        if target.exists() and target.stat().st_size:
            occupied = self._occupant_summary(target)
            if occupied and not force:
                raise CommandError(
                    f"{target} already contains data ({occupied}).\n"
                    "This command will not overwrite existing work. Either:\n"
                    "  * delete/rename the file yourself and re-run, or\n"
                    "  * re-run with --force (a timestamped backup is kept)."
                )
            if occupied:
                backup = target.with_name(
                    target.name + ".before-seed-" + target.stat().st_mtime_ns
                )
                shutil.copy2(target, backup)
                self.stdout.write(self.style.WARNING(f"backed up {target} -> {backup.name}"))

        target.parent.mkdir(parents=True, exist_ok=True)
        staged = target.with_name(target.name + ".installing")
        shutil.copy2(extracted, staged)
        os.replace(staged, target)
        self.stdout.write(self.style.SUCCESS(f"installed seed database -> {target}"))
        return target

    def _occupant_summary(self, path: Path) -> str:
        try:
            probe = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
        except sqlite3.Error:
            return ""
        try:
            parts = []
            for table in ("tourist_user", "tourist_destination"):
                try:
                    count = probe.execute(f'select count(*) from "{table}"').fetchone()[0]
                except sqlite3.Error:
                    continue
                if count:
                    parts.append(f"{table}={count}")
            return ", ".join(parts)
        finally:
            probe.close()

    def _report(self, target: Path) -> None:
        # Point this process at the freshly installed file, then always put the
        # connection back so the rest of the process (and test teardown) still
        # sees the database it started with.
        previous = connection.settings_dict.get("NAME")
        connection.close()
        settings.DATABASES["default"]["NAME"] = str(target)
        connection.settings_dict["NAME"] = str(target)
        try:
            call_command("migrate", interactive=False, verbosity=0)
            self._print_summary()
        finally:
            connection.close()
            settings.DATABASES["default"]["NAME"] = previous
            connection.settings_dict["NAME"] = previous

    def _print_summary(self) -> None:
        summary = database_path()
        probe = sqlite3.connect(summary)
        try:
            self.stdout.write("")
            self.stdout.write(self.style.SUCCESS("Seed database ready."))
            for table in (
                "tourist_destination",
                "tourist_destinationimage",
                "tourist_hotel",
                "tourist_hospital",
                "tourist_policestation",
                "tourist_restaurant",
                "tourist_osmessentialservice",
                "tourist_destinationtransitroute",
                "tourist_managedpage",
                "tourist_contentsection",
                "tourist_user",
            ):
                try:
                    count = probe.execute(f'select count(*) from "{table}"').fetchone()[0]
                except sqlite3.Error:
                    continue
                self.stdout.write(f"  {table}: {count}")
        finally:
            probe.close()

        self.stdout.write("")
        self.stdout.write(
            "Hotels, hospitals, police stations and restaurants are imported as "
            "unverified candidates and stay hidden from the public API until a "
            "staff member verifies them in the admin. That is expected."
        )
        self.stdout.write(
            "No accounts are included. Create your own login with: "
            "python manage.py createsuperuser"
        )
