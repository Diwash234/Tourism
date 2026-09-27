NEPAL YATRA — PUBLIC DATABASE DOWNLOADS
======================================

This directory contains the shareable, privacy-safe database artifacts.  It is
not a copy of the live operational database.

Files
-----

* nepal-tourism-database.sqlite3.gz — deterministic compressed SQLite snapshot
  (the canonical release; built from the JSON catalog below)
* nepal-tourism-database.sqlite3.gz.sha256 — checksum for the archive
* nepal-tourism-seed.sqlite3.gz — ready-to-run seed database for a new clone
* nepal-tourism-seed.sqlite3.gz.sha256 — checksum for the seed archive
* ../Tourism/dataset/verified_tourism_data.json — canonical JSON catalog used
  to build the archive
* ../Tourism/dataset/verified_tourism_data.json.sha256 — checksum for the JSON
* ../Tourism/dataset/verified_tourism_data.schema.json — JSON contract
* ../Tourism/dataset/verified_tourism_data.lock.json — release lock/counts

The JSON catalog and SQLite archive are generated as one pair.  The SQLite file
is built into a fresh migrated database from the JSON, then both artifacts are
compared record-for-record before publication.  A database row count or image
count printed in an old report is not a source of truth; use the JSON metadata
and checksums for the current release.

New clone: get the data in one command
---------------------------------------

A clone receives the code, not a database.  To install the published seed
database (destinations, galleries, hotels, hospitals, police stations,
restaurants, OSM services, transit routes and published CMS pages):

    git clone https://github.com/Diwash234/Tourism.git
    cd Tourism/Tourism
    python manage.py install_public_seed_db

The command verifies the archive checksum, SQLite integrity and foreign keys,
refuses to overwrite a database that already has users or destinations, and
then prints the imported row counts.  It contains no accounts, so create your
own login afterwards:

    python manage.py createsuperuser

Hotels, hospitals, police stations and restaurants arrive as sourced but
unverified listings and stay labelled as unverified until a staff member
verifies them in the admin.

Privacy boundary
----------------

The public snapshot excludes users, password hashes, sessions, JWTs, email
verification data, device tokens, chat, bookings, orders, location history,
notifications, audit/log records, drafts, reviewer IDs, local media paths, and
service records located outside Nepal.  Since policy version 2, sourced
hotels, restaurants, hospitals, police stations and essential services are
included with their stored is_verified flag; unverified ones are labelled
"Unverified listing" on the website and are never marked verified.  Do not publish `Tourism/db.sqlite3`; it is
runtime state and is intentionally ignored by Git.

A missing image is shown as unavailable.  The catalog does not substitute a
photo from another destination, and AI-generated or user-uploaded images are
not promoted into the public verified-media set.

Build or verify
---------------

From the repository root, stop the application if the source database is being
written, then run:

    cd Tourism
    python manage.py build_verified_snapshot \
      --as-of 2026-09-25T23:59:59Z \
      --force

The command takes an online SQLite backup, migrates only the temporary copy,
exports the allowlisted JSON, creates a fresh database, loads the JSON, runs
Django checks and SQLite integrity checks, and publishes the JSON/archive
atomically.  It never copies the raw runtime file into the release.

Verify an existing pair without rebuilding:

    cd Tourism
    python manage.py verify_verified_snapshot \
      ../Tourism/dataset/verified_tourism_data.json \
      --database ../downloads/nepal-tourism-database.sqlite3

For a local development database, use a separate file and create an admin
explicitly:

    python manage.py migrate
    python manage.py createsuperuser

No default administrator credentials are shipped in the download.
