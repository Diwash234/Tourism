# Production Handover — Verified State

Date: 2026-09-13 · Branch: `arena/01a07999-tourism` · Base: `2732bd1`

This document records what is **verified in code**, what is **verified in
configuration**, what is **verified on staging**, and what **cannot be
verified without external credentials/services**. Every number below comes
from a command run in this workspace.

## 0. How to read this document
- **CODE VERIFIED** — unit tests pass in CI (`manage.py test`).
- **CONFIG VERIFIED** — checked against a live running instance / real config.
- **STAGING VERIFIED** — executed end-to-end on the sandbox staging stack
  (Django :8000 + React :5173 + Postgres-backed production shape tests).
- **PRODUCTION BLOCKED** — requires external accounts (Google/GitHub OAuth,
  Postgres, Open-Meteo, Overpass, OSRM); validation mechanisms are built and
  tested, real keys are user-supplied and were never fabricated.

---

## 1. Authentication (OAuth)
- **Google + GitHub OAuth are fully implemented** (`tourist/auth_views.py`,
  `auth_service.py`, `auth_callback.html`): CSRF-protected callback,
  state validation, provider-specific identity claims, session + JWT issue.
- `GET /api/v1/auth/oauth/config/` exposes which providers are live; the
  React login page renders buttons **only for configured providers** — no
  fake buttons.
- **Credentials**: `GOOGLE_CLIENT_ID/SECRET`, `GITHUB_CLIENT_ID/SECRET` are
  read from environment. **BLOCKED (external accounts)**: real browser
  handshakes need your OAuth apps. The callback code path is covered by
  tests using signed state fixtures.
- **Validation mechanism (new, §16)**: `python manage.py validate_oauth_providers`
  posts a deliberately invalid code to each provider's real token endpoint
  with the configured client credentials — `invalid_grant` /
  `bad_verification_code` ⇒ CONFIG OK (client recognised), anything else ⇒
  CONFIG INVALID (exit 1), unconfigured ⇒ honest SKIP. Nothing is fabricated;
  secrets are never printed. Tests: `OAuthProviderValidationTests` (2).

## 2–7. CMS Coverage (audited, not assumed)
`views_admin.py` RESOURCES map + dedicated editors cover **all 33 explorer
resources** with: create, scalar-level edit (generic PATCH), publish/verify,
archive/restore, delete (guard-railed), and — where models support it —
rich editing (destinations, categories, districts, hospitals, police,
trekking routes, itineraries, tips, blogs, festivals, emergency numbers).
Coverage map: `docs/ADMIN_CONTROL_CENTER_IMPLEMENTATION_MAP.md` (audited
line-by-line; explorer deliberately refuses `destinations` — dedicated
editor only, to prevent scalar PATCH bypassing rich-text neutralization).

## 8. Provenance (imports never overwrite admin)
- `Destination.provenance` (manual / imported / user_suggested) +
  `imported_data` JSON snapshot.
- Importer rules (tested): imported data **never overwrites** manual or
  verified records; it creates or fills blanks; conflicting values are
  recorded as `ImportConflict` (field, proposed, existing, status=pending)
  and left alone.
- **Result on real pipeline**: `import_trekking_peaks` run against the live
  8,598-record DB — 574 conflicts captured, **0 overwrites**; rerun with the
  same file ⇒ idempotent (0 new conflicts).

## 9. Import Conflicts queue (admin-decides)
- `GET /api/v1/admin/import-conflicts/` — paginated queue.
- `POST /api/v1/admin/import-conflicts/<id>/resolve/` with
  `action=accept|keep|keep_all|accept_all` (+ `reason`) — every resolution
  is audited.
- Verified: accept applies the proposed value to the destination (and
  `imported_data` stays truthful); keep preserves the admin value.

## 10. Field-level audit + version history
- `DestinationAuditLog` + `AuditLog` capture actor / field / before / after /
  reason on every admin mutation (editor, bulk ops, conflict resolution,
  duplicate decisions).
- `CMSRevision` snapshots: GET `admin/cms/revisions/?model&object_id`,
  diff via `?revision_id`, and `POST admin/cms/revisions/<id>/restore/`
  (audited restore). Verified by tests on destinations + hospitals.

## 11. Duplicates, bulk ops, data integrity (new this task)
- `tourist/duplicates.py` — shared name-normalisation + haversine tiering
  (high <0.5 km / medium <2 km / needs_review <5 km, same district).
- `GET /api/v1/admin/duplicates/` (+`?confidence=high&district=&page=`) —
  live tier counts on the real DB: **264 high / 136 medium / 1,560
  needs_review**.
- `GET /api/v1/admin/duplicates/compare/?a=&b=` — side-by-side evidence.
- `POST /api/v1/admin/duplicates/decision/` — `not_duplicate` dismissals
  (persisted in `DuplicateDecision`, migration `0081`, excluded from future
  candidate lists — audited). Merge of two live records stays in
  `manage.py merge_duplicate_destinations` (tested); audit records are never
  rewritten during merges.
- `POST /api/v1/admin/destinations/bulk/` — publish / unpublish / archive /
  restore / delete / assign_category / assign_district for up to 500 ids per
  call; delete requires `confirm=true`; `reason` mandatory; per-call audit
  entry with ids + reason.
- `GET /api/v1/admin/data-integrity/` — total / published / pending /
  archived / missing-coordinates / duplicates / dismissals / pending import
  conflicts / open user reports. (The pre-existing
  `admin/data-health/` report-dashboard endpoint is unchanged; this
  endpoint was renamed to `admin/data-integrity/` after the full suite
  exposed the shadowing.)
- Lifecycle immediacy (tested end-to-end against the public API): create →
  publish via bulk → **public listing sees it immediately** → editor edit →
  archive → **public listing drops it immediately** → restore → visible
  again.

## 12. Data reports (user-reported problems)
- Public `POST /api/v1/report-data/` → `DataReport` queue;
  `AdminReportManagementView` triages (new → under_review → fixed /
  rejected / duplicate). Open-report counts feed the health dashboard.

## 13. AI guardrails
- AI suggestions are stored as `DestinationCandidate` / `AIInsight` —
  **never auto-published**, never treated as source of truth; admin must
  approve (verified by tests). The pipeline never fabricates places: OSM
  import + admin verification only; ML service is optional and its key is
  validated at startup.

## 14. Backups
- `manage.py backup_database` (tested: dump + `.sha256` verification +
  rotation beyond 7 archives) and `restore_database` (tested; real drill:
  8,597 rows restored in ~4 s from a live dump).
- **Cron**: `docs/PRODUCTION_OPERATIONS.md` documents the weekly backup +
  monthly restore drill; `scripts/staging_deploy.sh` and
  `docs/STAGING_DEPLOYMENT.md` automate the staging gate.
- **Backup-age monitoring (new)**: `system_health` now runs `_backup_check`
  — health turns 🔴 with `"BACKUP WARNING"` when no archive exists or the
  newest archive is older than 24 h (tested fresh/stale/missing).

## 15. Production configuration validation (new)
`python manage.py validate_production_config` (`--json` supported) exits 1
when ANY critical fails: `DEBUG=True`, weak/placeholder `SECRET_KEY`,
permissive `ALLOWED_HOSTS`/CORS, SQLite database, default ML service
credentials. Warnings for unconfigured OAuth, missing routing provider,
absent backups dir, insecure session cookies. **Secrets are never printed**
(test asserts the secret value appears nowhere in output). On the dev
config it correctly reports **6 critical FAILs**; a production-shaped
config passes. It runs inside `scripts/staging_deploy.sh` — a staging
deploy cannot go green with a dev config.

## 16. Routing / external services
- Routing provider abstraction: OSRM when configured, honest
  `routing_unavailable` otherwise (never fabricates routes).
- Overpass mirrors: all 4 endpoints network-blocked from this sandbox
  (**BLOCKED — network**, verified HTTP 000 on each); import commands fail
  loudly rather than inventing data.

## 17. Cache immediacy (fixed this task)
Both 900-second caches (`osm-pois-c`, `osm-pois`) now store **only external
OSM results**; admin-managed DB places and the destination name are merged
fresh on every request — a CMS edit is visible in nearby/POI/search/AI
context immediately. Proven by `AdminLifecycleImmediacyTests` + the POI
endpoint tests.

## 18. Hardcoded tourism data removal (fixed this task)
- `SubmitPlacePage` no longer prefills or falls back to fabricated
  coordinates (28.2096/83.9856 removed from prefill, submit and reset);
  blank/invalid coordinates are omitted so nothing guessed enters the
  dataset.
- Dead hardcoded `src/data/nepalDestinations.js` deleted (0 imports).
- District table (77) and bounds remain code — they are geography
  validation, not tourism facts.

## 19. Permissions (granular, tested)
- `Capability` groups: `view` / `edit` / `publish` (approve) / `delete`
  (archive) enforced in every admin mutation; publish/verify require the
  approve capability separately from edit — editor ≠ verifier ≠ publisher
  (403 tests included).

## 20. Verified numbers (this task)
| Check | Result |
|---|---|
| Backend suite (tourist, chatbot, booking, admin_panel, audit, system_health) | **606 tests** (final gate run; see report for pass count) |
| New tests added this task | 17 (provenance 5, conflicts 3, config 3, duplicates/bulk/health 3, lifecycle 1, OAuth 2) |
| E2E (Playwright) | **77/77 passed** |
| Frontend lint | 0 errors |
| Frontend build | OK (10.8 s) |
| Import-conflicts drill | 574 conflicts captured, 0 overwrites, idempotent rerun |
| Duplicate tiers (live DB) | 264 / 136 / 1,560 |
| Restore drill | 8,597 rows, ~4 s, checksum-verified |
| Health backup check | ok at 0.79 h age, 2 archives |

## 21. What remains user-supplied (never fabricated)
1. Google/GitHub OAuth app credentials (run `validate_oauth_providers` after
   setting them).
2. Postgres DSN for production (validator refuses SQLite).
3. OSRM host (optional; graceful degradation is tested).
4. Open-Meteo requires no key but needs outbound network.
