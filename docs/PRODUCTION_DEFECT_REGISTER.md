# Production Defect Register

Live register for the remediation arc ending at the current branch tip.
Every "Fixed" entry names the commit, the observed evidence, and the test
that now covers it. Open entries stay open until a test proves otherwise.
Severity: P0 security/data corruption · P1 major user-facing · P2 important
· P3 minor.

| ID | Sev | Area | Observed | Root cause | Fix / Evidence | Test | Status |
|----|-----|------|----------|-----------|----------------|------|--------|
| DEF-001 | P1 | Datastore | Any real PostgreSQL crashed loading OSM data: `integer out of range` on Destination insert | `Destination.external_id` was `IntegerField`; 4,347/6,654 OSM ids exceed int4 max | BigIntegerField migration `0071` (commit `21aeb45`); 480/480 tests on PostgreSQL 18.4 | Full suite run on real PG (`DATABASE_URL=postgres://…`) | Fixed |
| DEF-002 | P2 | Backup | `backup_database` crashed with `FileNotFoundError: pg_dump` when client tools off PATH | Bare binary name in subprocess call | `PG_DUMP` env → PATH lookup → actionable CommandError (`21aeb45`) | `BackupRestoreTests` on PG | Fixed |
| DEF-003 | P1 | Restore | Postgres backups were unrestorable (SQL dump fed to JSON `loaddata`) | `restore_database` had no SQL path | Real SQL restore: checksum-gated drill + `--confirm` live rebuild (`21aeb45`) | `BackupRestoreTests` roundtrip on PG | Fixed |
| DEF-004 | P1 | Navigation | ALL routes degraded to straight-line estimates; bundled corridor graph never used | `BundledGraphProvider` expected list/tuple points but `best_route()` returns `{'lat','lng'}` dicts → geometry parsed empty → silent `None` | Parse dicts; surface engine's per-waypoint directions as real steps with maneuver keys + landmark names (`2a15f61`) | `navigation` suite (30 tests); audit smoke routes now `graphml_fallback` | Fixed |
| DEF-005 | P1 | Nearby services | `destinations/<ref>/nearby-pois/` returned 503 dead end when Overpass unreachable | No offline fallback | DB-backed fallback (hospitals/police/stays/categories), always 200, honest provenance; unbacked categories empty **with note** (`2a15f61`) | `DestinationNearbyPOIsFallbackTests`; regression test re-pinned to new contract | Fixed |
| DEF-006 | P2 | Itineraries | Offline itinerary builder ignored canonical `district` (matched only free-text `city`, mostly blank) → weak plans for most of the 77 districts | Query used `city__icontains` only | Matches district too, quality-ordered, interest-aware (`2a15f61`) | `OfflineItineraryAllCitiesTests` (Mustang, Rautahat) | Fixed |
| DEF-007 | P2 | Datastore | SQLite ran `journal_mode=delete`, `foreign_keys=0` — not production-safe | Default SQLite pragmas | WAL + synchronous=NORMAL + FK ON + busy_timeout via `connection_created` (`37bfb61`); validator accepts hardened SQLite, rejects unhardened | `test_wal_hardening_applied_to_file_backed_sqlite` (real subprocess) | Fixed |
| DEF-008 | P2 | Config | `close_production_gates.sh` gate 6 advertised `DATABASE_URL` but settings never read it — gate was dead on any host | Settings only knew `DB_ENGINE`/`DB_*` | `DATABASE_URL` parsing (postgres://, sqlite://) with precedence (`37bfb61`) | `test_database_url_parsing`; PG suite driven through `DATABASE_URL` | Fixed |
| DEF-009 | P2 | Migrations | Tracked `db.sqlite3` was missing `navigation.0002` (`navigation_navigationsession`) — `dumpdata` crashed | Restored snapshot predated the migration | `migrate` applied; committed (`21aeb45`) | dumpdata/loaddata 9,531-object transfer to PG | Fixed |
| DEF-010 | P3 | Data quality | 8 coordinate clusters (>3 records sharing a point) | Curated seed used area-level points | 38 records honestly marked `APPROXIMATE / 'Area Point'`; audit exempts marked clusters only (`29783e5`) | `audit_navigable_places` (0 unmarked clusters) | Fixed |
| DEF-011 | P3 | Data quality | 190 approved records share name+district pairs (e.g. duplicate "Hotel Vinayak" in Mahottari) | OSM import duplicates not yet deduplicated | Duplicate-detection infra exists (`DuplicateDecision`, discovery pipeline); merge pass not yet run | reported in `reports/live_data_quality.json` | **Open** |
| DEF-012 | P3 | Data quality | 1,641 public records have blank `district` (city text present for some) | OSM import lacked district assignment; normalizer refuses to fabricate | Needs sourced geocoding (ward/municipality → district), not guesswork | `missing_district` tracked in data-quality report | **Open** (by design — no fabrication) |
| DEF-013 | P3 | Frontend | Single 2.4 MB JS bundle (674 KB gzip) | No route-level code splitting | Build warns; splitting not yet done (must not break features) | build output measured | **Open** |
| DEF-014 | P2 | Test hygiene | Live E2E leaked probe records into the production DB — 15 accumulated `E2E Probe/Lifecycle` rows found in db.sqlite3 (this run) | Probe cleanup only *rejected* entries; lifecycle delete existed but earlier runs predated it | Purged 15 records; `live.mjs` probe cleanup now hard-deletes via admin bulk endpoint after the media step reuses it (`13fbf04`+) | E2E 67/67 with `E2E %` DB count = 0 after run | Fixed |
| DEF-015 | P2 | Data integrity | Hard-deleted destinations lingered as ghosts in the authoritative `dataset/data.json` snapshot | `sync_admin_destination_json` upserts only; bulk delete never pruned | New `remove_admin_destination_json()` wired into bulk delete; E2E run now leaves snapshot record-count unchanged | `DataJsonSnapshotPruneTests`; live E2E proof (create→sync→delete→prune, count back to 14) | Fixed |

## Gate-level blockers (not defects — external dependencies)

| Item | Status | Evidence | Closes with |
|---|---|---|---|
| Live OSRM street routing | PARTIAL | `router.project-osrm.org` unreachable from CI sandbox (`SSL_ERROR_SYSCALL`, re-verified 2026-09-20); offline fallback is labelled node-level | `ROUTING_BASE_URL` + `validate_navigation_routes --write-baseline` on host |
| Playwright browser E2E | BLOCKED | cdn.playwright.dev **and** npmmirror both TLS-blocked; no root for system deps; only npm/PyPI/GitHub reachable | `npx playwright install --with-deps` on host |
| Physical-device GPS | BLOCKED | requires real hardware | manual run per `docs/DEPLOYMENT_GUIDE.md` §6 |
| Live weather / OAuth / DHM / BIPAD | PARTIAL (paths mock-verified) | no credentials in sandbox; `validate_oauth_providers` + `OAuthCallbackFlowTests` cover code paths | real keys/credentials on host |
