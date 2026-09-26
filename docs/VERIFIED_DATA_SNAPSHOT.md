# Verified public data snapshot

`Tourism/dataset/verified_tourism_data.json` is the versioned public data
contract. The compressed database in `downloads/` is generated from that JSON;
the live `Tourism/db.sqlite3` is operational state and is not a release source.
`verified_tourism_data.lock.json` binds the JSON, database, cutoff, counts, and
checksums as one release.

## Two tracked databases, two jobs

| Artifact | Job |
| --- | --- |
| `downloads/nepal-tourism-database.sqlite3.gz` | canonical release: built from the JSON catalog under the data policy below, score-gated media, checksummed against the lock file |
| `downloads/nepal-tourism-seed.sqlite3.gz` | working seed for a new clone: the full public catalogue, ready to run |

The canonical release is the publication contract and is the artifact to verify
or diff. The seed database answers a different question — "a collaborator just
cloned this, how do they get data?" — so it is not built from the JSON catalog
and is not part of the lock file. It carries the same public content with the
media rows the app can actually display, and it is installed with one command:

```bash
git clone https://github.com/Diwash234/Tourism.git
cd Tourism/Tourism
python manage.py install_public_seed_db      # verifies checksum, then installs
python manage.py createsuperuser             # the seed has no accounts
python manage.py runserver
```

`install_public_seed_db` checks the archive SHA-256, SQLite integrity and
foreign keys before writing anything, refuses to overwrite a database that
already has users or destinations (`--force` keeps a timestamped backup), and
prints the imported row counts. `--verify-only` inspects the archive without
installing it. If you prefer to place the file by hand, the `gunzip` recipe in
"Use the shared database locally" below still works.

The seed database never contains accounts, password hashes, tokens, sessions,
chats, bookings, notifications, audit logs, drafts or local media paths, and it
never promotes a place to verified: unverified listings arrive unverified and
stay hidden from the public API until staff verify them.

## One-way release flow

```text
live SQLite (read-only online backup)
        ↓
temporary migrated copy
        ↓
allowlisted JSON catalog + SHA-256
        ↓
fresh migrated SQLite
        ↓
record equality / privacy / Django / SQLite checks
        ↓
JSON + compressed SQLite + checksums
```

The release is a one-way promotion. Never merge the public catalog into a
populated runtime database and never copy a raw runtime SQLite file to Git.

## Build

From `Tourism/`:

```bash
python manage.py build_verified_snapshot \
  --source-db /path/to/source.sqlite3 \
  --as-of 2026-09-26T00:00:00Z \
  --force
```

`--as-of` is required so scheduled/published records have an explicit release
cutoff. Use a new cutoff for each release. The builder:

1. takes an online SQLite backup without modifying the source;
2. migrates and reindexes only the temporary copy;
3. exports only allowlisted, public records;
4. creates a fresh database and loads the JSON;
5. compares the canonical record digest;
6. runs Django checks, foreign-key checks, and SQLite integrity checks;
7. publishes outputs atomically.

The runtime database may continue serving requests while the online backup is
taken, but a release should be built from a quiet database when possible.

## Data policy (policy version 2)

Included records must be sourced and public:

- active, approved, non-user-submitted destinations with a slug or external ID
  and valid Nepal coordinates;
- published CMS records and active public navigation;
- **services** — hotels, restaurants, hospitals, police stations and OSM
  essential services (banks, ATMs, pharmacies…) — that come from a named
  source, whether or not an administrator has verified them yet. Each record
  keeps its stored `is_verified` flag exactly: an unverified listing is
  published *as unverified* and the website labels it "Unverified listing ·
  Source: …" and lists verified records first. Nothing is ever promoted to
  verified by the snapshot. Coordinates are optional for a service, but when
  present they must be inside Nepal (records located abroad are dropped).
  Exact duplicate imports (same name, coordinates and destination) are
  published once;
- approved external images with HTTPS URLs, source/license metadata, and,
  **depending on the active media gate**, either both `destination_match_score`
  and `authenticity_score` of at least `0.85` assigned by a named reviewer, or
  simply the application's own rule (approved, verified, destination-specific).

The media gate is explicit and configurable — see
[MEDIA_REVIEW.md](MEDIA_REVIEW.md). Choose it per release:

```bash
# Match the release to the rule the running application already applies
PUBLIC_SNAPSHOT_MEDIA_GATE=approval python manage.py build_verified_snapshot --as-of ... --force

# Keep the scored rule and require a completed human media review
PUBLIC_SNAPSHOT_MEDIA_GATE=scored python manage.py build_verified_snapshot --as-of ... --force
```

The active rule is recorded in every release as `policy.media_gate`, and
`python manage.py snapshot_media_exclusions` reports why any record is excluded.
No option invents a score: import paths leave scores `NULL` and the record
reports as awaiting media review.

Why v2: policy v1 published only verified services. No imported hotel had been
verified, so the shared database contained no hotels at all and every
"Hotels near…", distance and itinerary-stay panel reported that the service
did not respond. Showing sourced listings with an honest label is more useful
than an empty page, and it never presents unconfirmed data as confirmed.

Service `source_name` values are cleaned: legacy image-credit notes that were
stored in that column are removed, and a record with no source left is
labelled "Imported project dataset (not yet verified)".

Excluded records include credentials, users, sessions, tokens, chats, bookings,
orders, location history, notifications, audit/log data, drafts, reviewer IDs,
local media paths, synthetic E2E/demo/fixture records, and services located
outside Nepal.

Missing data remains missing. The snapshot does not invent a hotel, hospital,
restaurant, phone number, coordinate, or image. Coverage gaps are real: for
example the OSM pharmacy extract only covers the Kathmandu Valley, so the
emergency page shows no pharmacies near Pokhara.

## Current release

| | |
|---|---|
| Policy version | 2 |
| Cutoff (`--as-of`) | `2026-09-26T00:00:00Z` |
| Source database | `git show f92c128^:Tourism/db.sqlite3` (the last committed runtime DB, read-only) |
| JSON records | 12,933 |
| Destinations | 6,075 |
| Destination images | 723 (quality-scored) |
| Hotels | 2,348 (all unverified, labelled) |
| Restaurants | 265 |
| Hospitals | 362 |
| Police stations | 801 |
| OSM essential services | 1,997 (banks 838, ATMs 346, hospitals 381, pharmacies 351, police 81) |
| Districts / provinces | 77 / 7 |

Checksums live in `verified_tourism_data.lock.json` and the `.sha256` files.

### Never "fix" a checksum mismatch by re-committing the file

The release artifacts are declared `-text` in the repository `.gitattributes`, so
Git stores and checks out their exact bytes on every platform. This matters:
with the Windows default `core.autocrlf=true`, Git rewrites LF to CRLF on
checkout, which changes those bytes and makes a working-tree hash disagree with
the published `.sha256` even though nothing was actually modified. Observed
locally on a clean checkout of a good commit:

```
sidecar 9be511a1a54a6461...
on disk (CRLF checkout) -> mismatch
```

Re-committing the file to "fix" that would rewrite every published byte while
the diff looked empty, breaking the download links and failing both the CI
artifact check and `verify_verified_snapshot`. If you see a checksum mismatch:

1. Confirm it is not a line-ending artifact by hashing the committed blob
   instead of the working tree:
   `git cat-file blob HEAD:Tourism/dataset/verified_tourism_data.json | sha256sum`
2. If the blob matches, nothing is wrong - do not commit the file.
3. If the blob genuinely differs, rebuild the release as a pair
   (`build_verified_snapshot`) so the JSON, the SQLite archive and all three
   checksum files are regenerated together. Never hand-edit a checksum.

## Use the shared database locally

```bash
cd Tourism
rm -f db.sqlite3 db.sqlite3-wal db.sqlite3-shm   # stale WAL files corrupt a swapped DB
gunzip -c ../downloads/nepal-tourism-database.sqlite3.gz > db.sqlite3
python manage.py migrate
DJANGO_SUPERUSER_PASSWORD='choose-one' python manage.py createsuperuser --noinput --email you@example.com
python manage.py runserver 0.0.0.0:8000
```

The snapshot has no users, so create your own administrator. Restart the
server after swapping the file.

If the old raw SQLite file was ever cloned or deployed, deleting it from the
current tree does not remove it from Git history or invalidate its sessions and
JWTs. Rotate affected passwords/tokens and treat that historical artifact as
sensitive.

## Identity and numeric IDs

`slug` and `external_id` are the destination identity used for cross-database
matching. Django numeric primary keys are snapshot-local implementation details
and are valid only inside this matched JSON/database pair. They must not be
used to merge independently rebuilt databases. The payload records this rule
in `identity_policy`.

## Verify

```bash
python manage.py verify_verified_snapshot \
  dataset/verified_tourism_data.json \
  --database ../downloads/nepal-tourism-database.sqlite3
```

When the database is the active Django database, omit `--database`:

```bash
python manage.py verify_verified_snapshot dataset/verified_tourism_data.json
```

A successful result means the JSON and database have the same canonical record
digest, contain no users, contain no out-of-Nepal public destination, pass
Django checks, and pass SQLite integrity checks.

## Local development

The runtime database is intentionally ignored. Create a separate local file
and an administrator explicitly:

```bash
cd Tourism
python manage.py migrate
python manage.py createsuperuser
```

Do not use demo credentials in a public build. The `setup_system` command is
for local/bootstrap data experiments and is not a public release procedure.

## Legacy files

`dataset/data.json`, `dataset/destination_locations.json`, and
`tourist/verified_wikimedia_photos.json` are legacy projections/experimental
manifests. They are not synchronized into the release and must not be treated
as canonical. Generate any future adapter from the versioned catalog rather
than independently querying or editing a runtime database.
