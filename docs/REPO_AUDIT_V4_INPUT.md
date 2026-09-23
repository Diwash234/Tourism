# Repository Audit — input for Master Prompt V4

**Branch to audit: `arena/01a07999-tourism`, tip `9c72396`** (NOT `arena/01a03355-tourism` —
that is an older session branch, tip `737ee8b9`; it is missing the entire CMS lifecycle,
77-district, and data-integrity work described below).

Every statement below was verified against the checked-out tree at `9c72396` in this
workspace. Numbers are live results from the development database (6,691 destination
rows), not estimates.

---

## 1. Current architecture

**Backend** — Django 5.0.6, `Tourism/` project. Django apps (directories with models/views):
`tourist` (core, 96 model classes), `safety` (4), `admin_panel`, `audit`, `booking`,
`chatbot`, `dataset`, `media_app`, `notifications`, `system_health`, `translation`.
REST via DRF under `/api/v1/…` (`tourist/urls.py`), JWT auth
(`rest_framework_simplejwt`), capability-based staff permissions
(`AdminCapability` checks in `tourist/views_admin.py`), SQLite dev DB
(`Tourism/db.sqlite3`), Postgres-ready via env (`DATABASE_URL`).

**Frontend** — React (Vite) at `frontend/Tourism/`: `src/{pages,components,api,services,context,hooks,i18n,routes,styles}`.
Single `axiosClient` (`src/api/`) talking to the Django API via relative URLs (dev proxy).
Admin is a route section (`/admin/*`) with panels: DataExplorerPanel (full CRUD editor),
ContentLifecyclePanel (publish workflow), MediaApprovals, PlaceApprovals, UserManagement,
CategoryTranslationPanel, etc.

**Side services** — `ml_service/` (FastAPI, advisory ML), `image-server/`, `image-search/`
(both optional; backend degrades gracefully without them).

## 2. What is already implemented (working, tested)

- **Destinations**: 6,691 rows, all 77 districts, all categorized (0 null categories),
  full public API with pagination (`count/total_pages/current_page`), filters, search,
  map endpoints, detail with gallery/translations/reviews.
- **CMS lifecycle** (§ implemented and E2E-tested): DRAFT → (PENDING_REVIEW) → APPROVED
  publication states; admin-created records start as **draft, private**; explicit
  `POST /admin/destinations/<id>/lifecycle/` (publish/unpublish/archive/restore/
  submit_review); `GET …/preview/`; "why isn't this public?" diagnostics;
  revisions with restore; audit log; status counts on the list endpoint.
- **Search/Nearby**: `/api/v1/places/nearby/?lat&lng&radius_km&category` returns merged
  destinations + hospitals + police + hotels + landmarks (30 items verified at Pokhara
  center). `search-discover` endpoint with canonical public filter.
- **Itinerary**: `POST /api/v1/ml/itinerary/` — ML service when reachable, else an
  internal DB-driven fallback builder. **Verified live for all 77 districts at days=20:
  77/77 return 20 populated on-topic days.** Guarded by `DistrictItineraryTests`.
- **Hotels/Restaurants/Hospitals/Police**: models + endpoints + admin queues exist
  (`Hotel` line 917, `Hospital` 969, `PoliceStation` 999, `Restaurant` 1770 in
  `tourist/models.py`; safety app for hazards/alerts/reports).
- **AI (Himal AI)**: advisory only — recommendations carry
  `ai_recommendation_status` (models.py:639); publishing is a human admin action;
  partners cannot self-publish (403-tested in E2E).
- **Imports**: OSM import with conflict protection (`import_conflicts=0, total=6283`
  on re-import), duplicates detection, provenance tracking.
- **Tests**: backend 418 passing (`manage.py test tourist`), 61-check live E2E
  (`frontend/Tourism/e2e/live.mjs`) covering the 12-step acceptance scenario incl.
  full lifecycle journey, permissions 403s, media approval queue.

## 3. What is currently hard-coded (verified)

- **Frontend place data: none.** `src/data/` contains only `languages.js` +
  `phrases.js` (i18n phrasebooks — legitimate static content). No mock destination
  arrays remain; the DB is the source of truth.
- **Coordinates**: audited — 0 null, 0 outside Nepal bbox (26.3–30.5°N, 80–88.2°E)
  across 6,281 public rows. District centers live in
  `tourist/location/administrative_boundaries.py` (`NEPAL_DISTRICTS`, canonical 77).
- **Remaining honest hard-coding**: `start_city` defaults to `"Kathmandu"` in the
  itinerary serializer fallback (views_ml.py:553); hotel-context image fallbacks label
  generic photos honestly; ML service URL is env-driven with graceful fallback.

## 4. Connection chain React → API → Django → Models → DB

Fully connected for destinations, categories, lifecycle, media, approvals, safety,
users. The frontend uses relative URLs through the Vite dev proxy (no localhost calls
in browser code).

## 5. What should be preserved (do not rebuild)

Everything in §2. In particular: `Destination.publicly_visible()` (models.py) is the
**single canonical public-visibility rule** used by the public ViewSet and
search-discover; `verified_destination_photos()` enforces approved-only public media;
`normalize_district_names` and `categorize_existing` management commands; the
capability permission system; the E2E journey in `e2e/live.mjs`.

## 6. What specifically prevents nationwide scaling — actual remaining gaps

1. **External dependencies only you can provide**: OAuth credentials, production
   Postgres DSN + `SECRET_KEY`, cron entries on the real host, a host where
   `npx playwright install --with-deps` can run (browser specs; the API-level E2E
   already runs everywhere).
2. **Itinerary keys off `start_city` (string match on `city`)** — works for all 77
   districts today because imported records carry district names in `city`, but a
   district-first parameter would be more robust.
3. **ML itinerary service optional** — the DB fallback builder is simple (2 places/day,
   sequential); a real multi-day routing/planning service is the upgrade path.

## 7. Database architecture already present

SQLite (dev) / Postgres-ready. 96 tourist models incl. Destination (+96 fields:
coordinates, provenance, audit, AI advisory, translations M2M, gallery, embeddings),
DestinationImage (media approval states), DestinationNearbyPlace (currently empty —
nearby is computed, see §9), Category (37), Hotel/Restaurant/Hospital/PoliceStation,
DestinationAuditLog, Revision snapshots, ImportConflict, DuplicatePair, safety models.

## 8. Is there a canonical `Place` model?

**No — and none is needed yet.** `Destination` is the canonical place model (verified:
no `class Place(` exists anywhere in the backend). POI types (Hotel, Hospital,
PoliceStation, Restaurant) are separate related models. A unifying `Place` abstraction
is a legitimate V4 discussion item, but the current design works and is fully
API-exposed; unification would be a migration-heavy refactor, not a fix.

## 9. Do Navigation, Nearby and Itinerary share IDs? (verified — real gap)

- **Nearby** (`tourist/location/search_service.py`): items carry **synthetic prefixed
  ids**: `dest-<id>`, `hosp-<id>`, `pol-<id>`, `osm-<id>`, `landmark-<slug>` (lines
  163–265). The real PK is embedded but consumers must parse the prefix.
- **Itinerary** (`tourist/views_ml.py:582–588`): day items include **name, city,
  latitude, longitude, category — no id at all**. Linking itinerary stops to
  destination detail pages is currently name/coordinate-based.
- **Recommendation**: add `destination_id` (nullable, for non-destination POIs) to
  itinerary day items and a typed `{type, id}` to nearby items. Small, safe change.

## 10. Is AI authoritative or advisory?

**Properly advisory.** `Destination.ai_recommendation_status` stores AI state;
publication requires an explicit admin lifecycle action; E2E tests assert partners
cannot publish (403) and unapproved content never appears publicly.

---

### Suggested V4 prompt seeds (repo-specific, verified paths)

- "Add `destination_id` to itinerary day items in
  `Tourism/tourist/views_ml.py` (fallback builder ~line 582) and to ML-service passthrough,
  then make `frontend/Tourism/src/pages/Itinerary*` deep-link each stop to
  `/destinations/<slug>`."
- "Give nearby items a typed identity `{type: destination|hospital|police|hotel|landmark,
  id}` in `Tourism/tourist/location/search_service.py` (keep old string ids for
  compatibility) and consume it in the frontend nearby components."
- "Add an optional `district` parameter to the itinerary endpoint that filters
  `Destination.district` before the `city` fallback."
- "Do not rebuild: lifecycle (`views_admin.py`), public rule (`publicly_visible`),
  media approval (`verified_destination_photos`), district normalization
  (`normalize_district_names`), categorization (`categorize_existing`)."
