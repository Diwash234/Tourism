"""Safety tests for the public seed database installer.

The installer hands a stranger a database, so its guards are the point:
a tampered archive, a truncated archive, or an archive that still contains
accounts must all be refused, and an existing working database must never be
silently overwritten.
"""
from __future__ import annotations

import gzip
import hashlib
import sqlite3
import tempfile
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db.migrations.loader import MigrationLoader
from django.test import SimpleTestCase

from tourist.management.commands import install_public_seed_db as installer


def applied_migration_names() -> list[str]:
    """Every migration on disk, so a stand-in database needs no real migrating."""
    loader = MigrationLoader(None, ignore_no_migrations=True)
    return sorted(f"{app}.{name}" for app, name in loader.disk_migrations)


def build_database(path: Path, *, destinations=1200, images=1200, pages=1, users=0,
                   migrations=True) -> Path:
    """Create a minimal stand-in database with the tables the installer checks."""
    connection = sqlite3.connect(path)
    try:
        connection.execute("create table tourist_destination (id integer primary key)")
        connection.execute("create table tourist_destinationimage (id integer primary key)")
        connection.execute("create table tourist_managedpage (id integer primary key)")
        connection.execute("create table tourist_user (id integer primary key)")
        connection.executemany(
            "insert into tourist_destination (id) values (?)",
            [(i,) for i in range(destinations)],
        )
        connection.executemany(
            "insert into tourist_destinationimage (id) values (?)",
            [(i,) for i in range(images)],
        )
        connection.executemany(
            "insert into tourist_managedpage (id) values (?)",
            [(i,) for i in range(pages)],
        )
        connection.executemany(
            "insert into tourist_user (id) values (?)",
            [(i,) for i in range(users)],
        )
        if migrations:
            connection.execute(
                "create table django_migrations ("
                "id integer primary key autoincrement, app varchar, name varchar, applied datetime)"
            )
            connection.executemany(
                "insert into django_migrations (app, name, applied) values (?, ?, ?)",
                [
                    (name.split(".", 1)[0], name.split(".", 1)[1], "2026-01-01 00:00:00")
                    for name in applied_migration_names()
                ],
            )
        connection.commit()
    finally:
        connection.close()
    return path


def build_archive(workdir: Path, source_db: Path, *, sidecar: bool = True,
                  corrupt_sidecar: bool = False) -> Path:
    archive = workdir / installer.ARCHIVE_NAME
    with gzip.open(archive, "wb") as handle:
        handle.write(source_db.read_bytes())
    if sidecar:
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        if corrupt_sidecar:
            digest = "0" * 64
        sidecar_path = archive.with_suffix(archive.suffix + installer.SIDECAR_SUFFIX)
        sidecar_path.write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    return archive


class PublicSeedDbInstallerTests(SimpleTestCase):
    # The installer repoints the default connection at the file it just wrote,
    # so this suite needs query access even though it asserts on plain sqlite3.
    databases = {"default"}
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.workdir = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

        self.downloads = self.workdir / "downloads"
        self.downloads.mkdir()
        self.runtime = self.workdir / "db.sqlite3"

        self._original = (
            installer.archive_path,
            installer.sidecar_path,
            installer.database_path,
        )
        installer.archive_path = lambda: self.downloads / installer.ARCHIVE_NAME
        installer.sidecar_path = lambda: (
            self.downloads / (installer.ARCHIVE_NAME + installer.SIDECAR_SUFFIX)
        )
        installer.database_path = lambda: self.runtime

        self.addCleanup(self._restore)

    def _restore(self):
        (
            installer.archive_path,
            installer.sidecar_path,
            installer.database_path,
        ) = self._original

    def _source_db(self, **kwargs) -> Path:
        return build_database(self.workdir / "source.sqlite3", **kwargs)

    # -- guards --------------------------------------------------------------

    def test_corrupted_checksum_is_rejected(self):
        archive = build_archive(self.downloads, self._source_db(), corrupt_sidecar=True)
        self.assertTrue(archive.exists())
        with self.assertRaises(CommandError) as caught:
            call_command("install_public_seed_db")
        self.assertIn("Checksum mismatch", str(caught.exception))
        self.assertFalse(self.runtime.exists())

    def test_missing_checksum_is_rejected(self):
        build_archive(self.downloads, self._source_db(), sidecar=False)
        with self.assertRaises(CommandError) as caught:
            call_command("install_public_seed_db")
        self.assertIn("Checksum sidecar missing", str(caught.exception))
        self.assertFalse(self.runtime.exists())

    def test_truncated_database_is_rejected(self):
        build_archive(self.downloads, self._source_db(destinations=5, images=5))
        with self.assertRaises(CommandError) as caught:
            call_command("install_public_seed_db")
        self.assertIn("truncated", str(caught.exception))
        self.assertFalse(self.runtime.exists())

    def test_archive_containing_accounts_is_rejected(self):
        build_archive(self.downloads, self._source_db(users=3))
        with self.assertRaises(CommandError) as caught:
            call_command("install_public_seed_db")
        self.assertIn("tourist_user", str(caught.exception))
        self.assertFalse(self.runtime.exists())

    def test_existing_work_is_not_overwritten(self):
        build_archive(self.downloads, self._source_db())
        connection = sqlite3.connect(self.runtime)
        try:
            connection.execute("create table tourist_destination (id integer primary key)")
            connection.execute("insert into tourist_destination (id) values (1)")
            connection.commit()
        finally:
            connection.close()

        with self.assertRaises(CommandError) as caught:
            call_command("install_public_seed_db")
        self.assertIn("already contains data", str(caught.exception))

        # The original row must still be there.
        connection = sqlite3.connect(self.runtime)
        try:
            self.assertEqual(
                connection.execute("select count(*) from tourist_destination").fetchone()[0], 1
            )
        finally:
            connection.close()

    def test_corrupt_sqlite_payload_is_rejected(self):
        archive = self.downloads / installer.ARCHIVE_NAME
        archive.write_bytes(b"this is not a gzip stream")
        sidecar = self.downloads / (installer.ARCHIVE_NAME + installer.SIDECAR_SUFFIX)
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        sidecar.write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
        with self.assertRaises(CommandError):
            call_command("install_public_seed_db")
        self.assertFalse(self.runtime.exists())

    # -- happy path ----------------------------------------------------------

    def test_verify_only_does_not_install(self):
        build_archive(self.downloads, self._source_db())
        call_command("install_public_seed_db", verify_only=True)
        self.assertFalse(self.runtime.exists())

    def test_installs_seed_database(self):
        build_archive(self.downloads, self._source_db())
        call_command("install_public_seed_db")
        self.assertTrue(self.runtime.exists())
        connection = sqlite3.connect(self.runtime)
        try:
            self.assertEqual(
                connection.execute("select count(*) from tourist_destination").fetchone()[0],
                1200,
            )
            self.assertEqual(
                connection.execute("select count(*) from tourist_user").fetchone()[0], 0
            )
        finally:
            connection.close()
