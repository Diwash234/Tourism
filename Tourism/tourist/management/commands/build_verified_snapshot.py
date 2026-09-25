"""Build a matched canonical JSON + sanitized SQLite sharing snapshot.

The live/runtime SQLite file is never copied directly.  This command takes an
online SQLite backup, migrates that temporary copy, exports the safe JSON
contract, creates a fresh database, loads the JSON, verifies semantic equality,
and only then atomically publishes the JSON/compressed database artifacts.
"""
from __future__ import annotations

import gzip
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timezone as datetime_timezone
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, connections

from tourist.verified_snapshot import read_payload, sha256_file


class Command(BaseCommand):
    help = "Build a sanitized SQLite database and canonical JSON as one verified pair."

    def add_arguments(self, parser):
        default_db = connection.settings_dict.get("NAME", "")
        parser.add_argument(
            "--source-db",
            default=str(default_db),
            help="Source SQLite database. It is backed up read-only and never modified.",
        )
        parser.add_argument(
            "--json-output",
            default=str(Path(settings.BASE_DIR) / "dataset" / "verified_tourism_data.json"),
        )
        parser.add_argument(
            "--database-output",
            default=str(Path(settings.BASE_DIR).parent / "downloads" / "nepal-tourism-database.sqlite3.gz"),
            help="Compressed sanitized SQLite output path.",
        )
        parser.add_argument(
            "--raw-output",
            default="",
            help="Optional uncompressed SQLite output path (for example Tourism/db.sqlite3).",
        )
        parser.add_argument(
            "--lock-output",
            default=str(Path(settings.BASE_DIR) / "dataset" / "verified_tourism_data.lock.json"),
            help="Small manifest binding the JSON and compressed database checksums.",
        )
        parser.add_argument(
            "--as-of",
            required=True,
            help="Explicit ISO-8601 release cutoff, e.g. 2026-09-25T00:00:00Z.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Replace existing generated artifacts atomically.",
        )

    def handle(self, *args, **options):
        if connection.vendor != "sqlite":
            raise CommandError(
                "The snapshot builder currently requires a SQLite source. "
                "For PostgreSQL, export the same canonical JSON first and build a SQLite share artifact."
            )
        source = Path(options["source_db"]).resolve()
        json_output = Path(options["json_output"]).resolve()
        database_output = Path(options["database_output"]).resolve()
        raw_output = Path(options["raw_output"]).resolve() if options.get("raw_output") else None
        lock_output = Path(options["lock_output"]).resolve()
        outputs = [
            json_output,
            lock_output,
            database_output,
            database_output.with_name(database_output.name + ".sha256"),
        ]
        if raw_output:
            outputs.append(raw_output)
        existing = [path for path in outputs if path.exists()]
        if existing and not options["force"]:
            raise CommandError(
                "Refusing to replace existing snapshot artifacts without --force: "
                + ", ".join(str(path) for path in existing)
            )
        if not source.exists():
            raise CommandError(f"Source SQLite database not found: {source}")

        if raw_output and raw_output == source and source.exists():
            backup_dir = Path(settings.BASE_DIR) / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now(datetime_timezone.utc).strftime("%Y%m%d-%H%M%S")
            local_backup = backup_dir / f"db.sqlite3.before-verified-snapshot-{stamp}"
            shutil.copy2(source, local_backup)
            self.stdout.write(f"Local source safety backup: {local_backup}")

        with tempfile.TemporaryDirectory(
            prefix="nepal-yatra-snapshot-",
            ignore_cleanup_errors=True,
        ) as temporary_name:
            temporary = Path(temporary_name)
            migrated_source = temporary / "source-migrated.sqlite3"
            canonical_json = temporary / "verified_tourism_data.json"
            clean_raw = temporary / "nepal-tourism-database.sqlite3"
            compressed = temporary / database_output.name
            compressed_sha = temporary / (database_output.name + ".sha256")
            json_sha = temporary / (json_output.name + ".sha256")
            lock_file = temporary / lock_output.name

            self.stdout.write("1/7 Backing up source SQLite without modifying it...")
            self._backup_sqlite(source, migrated_source)
            self._run_manage(["migrate", "--noinput", "--verbosity", "0"], migrated_source)
            self._reindex_sqlite(migrated_source)

            self.stdout.write("2/7 Exporting canonical, privacy-safe JSON...")
            self._run_manage([
                "export_verified_snapshot",
                "--output",
                str(canonical_json),
                "--as-of",
                options["as_of"],
            ], migrated_source)
            payload = read_payload(canonical_json)

            self.stdout.write("3/7 Creating a fresh migrated database...")
            self._run_manage(["migrate", "--noinput", "--verbosity", "0"], clean_raw)

            self.stdout.write("4/7 Loading only canonical JSON records...")
            self._run_manage([
                "import_verified_snapshot",
                str(canonical_json),
                "--allow-empty-tourism-runtime",
            ], clean_raw)

            self.stdout.write("5/7 Verifying JSON/database equality and privacy gates...")
            self._run_manage([
                "verify_verified_snapshot",
                str(canonical_json),
            ], clean_raw)

            self.stdout.write("6/7 Compacting SQLite and checking integrity...")
            self._compact_sqlite(clean_raw)
            self._run_manage([
                "verify_verified_snapshot",
                str(canonical_json),
            ], clean_raw)

            self.stdout.write("7/7 Publishing matched artifacts...")
            self._write_deterministic_gzip(clean_raw, compressed)
            compressed_hash = sha256_file(compressed)
            compressed_sha.write_text(
                f"{compressed_hash}  {database_output.name}\n",
                encoding="utf-8",
            )
            json_hash = sha256_file(canonical_json)
            json_sha.write_text(
                f"{json_hash}  {json_output.name}\n",
                encoding="utf-8",
            )
            lock_file.write_text(
                json.dumps(
                    {
                        "format": "nepal-yatra-public-data-snapshot-lock",
                        "format_version": 1,
                        "as_of": payload["as_of"],
                        "minimum_tourist_migration": payload["minimum_tourist_migration"],
                        "records_sha256": payload["records_sha256"],
                        "counts": payload["counts"],
                        "artifacts": {
                            "json": {
                                "path": self._repo_relative(json_output),
                                "sha256": json_hash,
                            },
                            "database": {
                                "path": self._repo_relative(database_output),
                                "sha256": compressed_hash,
                            },
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                ) + "\n",
                encoding="utf-8",
            )

            # Nothing is published until every build/verification step above
            # has succeeded.  Each final file is replaced atomically.
            self._atomic_copy(canonical_json, json_output)
            self._atomic_copy(compressed, database_output)
            self._atomic_copy(compressed_sha, database_output.with_name(database_output.name + ".sha256"))
            self._atomic_copy(json_sha, json_output.with_name(json_output.name + ".sha256"))
            self._atomic_copy(lock_file, lock_output)
            if raw_output:
                if raw_output == source:
                    connections.close_all()
                self._atomic_copy(clean_raw, raw_output)

        counts = payload["counts"]
        self.stdout.write(self.style.SUCCESS(
            "Verified snapshot build complete: "
            f"{sum(counts.values())} JSON records, "
            f"{counts.get('tourist.destination', 0)} destinations, "
            f"{counts.get('tourist.destinationimage', 0)} quality-scored images, "
            f"JSON sha256={sha256_file(json_output)}, "
            f"DB sha256={compressed_hash}"
        ))

    def _run_manage(self, args: list[str], database: Path) -> None:
        env = os.environ.copy()
        # settings.py gives DATABASE_URL precedence over DB_NAME.  Explicitly
        # clear it so a developer shell cannot redirect this safety-critical
        # subprocess to PostgreSQL or another SQLite file.
        env["DB_ENGINE"] = "sqlite"
        env["DB_NAME"] = str(database)
        env["DATABASE_URL"] = ""
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        process = subprocess.run(
            [sys.executable, str(Path(settings.BASE_DIR) / "manage.py"), *args],
            cwd=settings.BASE_DIR,
            env=env,
            text=True,
            capture_output=True,
        )
        if process.returncode:
            if process.stdout:
                self.stdout.write(process.stdout)
            if process.stderr:
                self.stderr.write(process.stderr)
            raise CommandError(
                f"Snapshot subprocess failed ({' '.join(args)}) with exit code {process.returncode}."
            )

    @staticmethod
    def _repo_relative(path: Path) -> str:
        try:
            return str(path.relative_to(settings.BASE_DIR.parent)).replace("\\", "/")
        except ValueError:
            return str(path).replace("\\", "/")

    @staticmethod
    def _backup_sqlite(source: Path, destination: Path) -> None:
        source_uri = f"file:{source.as_posix()}?mode=ro"
        with sqlite3.connect(source_uri, uri=True, timeout=30) as source_db:
            with sqlite3.connect(destination, timeout=30) as destination_db:
                source_db.backup(destination_db)
        # Integrity is checked after REINDEX.  Older committed snapshots can
        # contain a damaged secondary index even while table rows are readable;
        # the temporary copy is repaired before any data is exported.

    @staticmethod
    def _reindex_sqlite(database: Path) -> None:
        with sqlite3.connect(database, timeout=30) as connection_obj:
            connection_obj.execute("REINDEX")
            result = connection_obj.execute("PRAGMA integrity_check").fetchone()[0]
        if result != "ok":
            raise CommandError(f"SQLite reindex integrity_check failed: {result}")

    @staticmethod
    def _compact_sqlite(database: Path) -> None:
        with sqlite3.connect(database, timeout=30) as connection_obj:
            connection_obj.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            connection_obj.execute("PRAGMA journal_mode=DELETE")
            connection_obj.execute("VACUUM")
            connection_obj.execute("PRAGMA optimize")
            result = connection_obj.execute("PRAGMA integrity_check").fetchone()[0]
        if result != "ok":
            raise CommandError(f"Compacted SQLite integrity_check failed: {result}")

    @staticmethod
    def _write_deterministic_gzip(source: Path, destination: Path) -> None:
        with source.open("rb") as input_handle, destination.open("wb") as raw_output:
            with gzip.GzipFile(
                filename="",
                mode="wb",
                compresslevel=9,
                fileobj=raw_output,
                mtime=0,
            ) as gzip_output:
                shutil.copyfileobj(input_handle, gzip_output, length=1024 * 1024)

    @staticmethod
    def _atomic_copy(source: Path, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(destination.name + ".tmp")
        shutil.copyfile(source, temporary)
        os.replace(temporary, destination)
