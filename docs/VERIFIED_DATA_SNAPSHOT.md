# Verified public data snapshot

`Tourism/dataset/verified_tourism_data.json` is the versioned public data
contract. The compressed database in `downloads/` is generated from that JSON;
the live `Tourism/db.sqlite3` is operational state and is not a release source.
`verified_tourism_data.lock.json` binds the JSON, database, cutoff, counts, and
checksums as one release.

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
  --as-of 2026-09-25T23:59:59Z \
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

## Data policy

Included records must be sourced and public:

- active, approved, non-user-submitted destinations with a slug or external ID
  and valid Nepal coordinates;
- published CMS records and active public navigation;
- explicitly verified hotels, restaurants, hospitals, police stations, and
  essential services (an unverified service is never promoted);
- approved external images with HTTPS URLs, source/license metadata, and both
  `destination_match_score` and `authenticity_score` of at least `0.85`.

Excluded records include credentials, users, sessions, tokens, chats, bookings,
orders, location history, notifications, audit/log data, drafts, reviewer IDs,
local media paths, synthetic E2E/demo/fixture records, and unverified services.

Missing data remains missing. The snapshot does not invent a hotel, hospital,
restaurant, phone number, coordinate, or image.

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
