# Nationwide Data Completion Report

Phase: **AUDIT → BUILD DATA PIPELINES → IMPORT REAL DATA → VERIFY → RE-AUDIT**
Started from commit `4614325` (frozen baseline). All numbers below were measured
against the live database on 2026-09-12 unless stated otherwise.

> **Headline honesty statement:** the import pipeline is built, tested, and
> idempotent — but **0 bulk OSM rows are imported yet**. This sandbox blocks
> direct TLS to Overpass mirrors, and the relay used to reach it degraded
> mid-session after 3 successful calls (8 consecutive failures afterwards).
> What was proven live: Nepal's OSM base contains **1,122 ATMs** (Overpass
> area count, `timestamp_osm_base 2026-09-12T05:14:30Z`). The moment extract
> files land in `Tourism/dataset/osm_raw/`, one command imports them.
> No fabricated records were created at any point.

---

## A. Repository

| Item | Value |
|---|---|
| Baseline commit | `4614325` |
| This phase commit | `7aee702` (+ this report commit) |
| Branch | `arena/01a07999-tourism` |
| Migrations | 76 applied (75 = extended service categories, schema no-op) |
| Backend tests | see §K |
| E2E | 77/77 |
| Build | ✓ (vite, 12.1s) |

## B. Import pipeline (built + tested this phase)

`python manage.py import_osm_services [--source DIR] [--dry-run] [--default-category X] [--report-dir DIR]`

- **Idempotent**: canonical key `osm_id = "<type>/<id>"` (unique). Proven by
  regression test: run 1 → created=1, run 2 → duplicate=1, created=0.
- **Validation gates**: Nepal bbox → nearest-district centroid ≤80 km
  (cross-border bleed inside a generous bbox is rejected: tested with a
  real Indian ATM coordinate) → category mapping → numeric-aware diff on
  re-runs (no spurious "updated").
- **Source tracking on every row**: `source_name="OpenStreetMap"`,
  `source_url=https://www.openstreetmap.org/<type>/<id>`, `raw_tags` JSON
  fidelity. Admin can always answer "where did this record come from?".
- **Reports**: `dataset/osm_reports/import_osm_services-<ts>.json` with
  found/created/updated/duplicate/rejected_* + by_category/by_province/by_district.
- **Dry-run**: supported and tested.
- **Category coverage**: atm, bank, restaurant, cafe, fast_food, bakery, bar/pub,
  pharmacy, hospital, clinic, doctors, dentist, police, fire_station, bus_station,
  fuel, charging_station, ambulance, blood_bank, taxi, supermarket, marketplace,
  guest_house/hostel, tourism information (26 category choices, migration 0075).

**Verified fetch procedure** (works through the relay when it is healthy):

```
https://overpass-api.de/api/interpreter?data=[out:json][timeout:300];
area["ISO3166-1"="NP"][admin_level=2][boundary=administrative]->.np;
nwr["amenity"="atm"](area.np);out skel center;
```
(URL-encode; swap `atm` per category; save JSON to `dataset/osm_raw/atm.json`;
then `manage.py import_osm_services --default-category atm`. The area query is
server-side scoped to Nepal — verified: 1,122 ATMs, zero India/China rows.)

## C. Data-quality backlog — measured, fixed where evidence-based

| Issue | Previous report | Measured today | Action |
|---|---|---|---|
| Duplicate name+coord clusters | "142" (looser metric) | **6 clusters / 6 extra rows** | all 6 = same district → **SAFE_MERGE**: higher id deactivated (status=rejected, IDs preserved, reversible); canonical = lower id |
| Name-only duplicate clusters | — | 345 clusters / 518 extra rows | classified ADMIN_REVIEW in `duplicate_report.csv` (common lodge/hotel names across districts — not safe to auto-merge) |
| Missing coordinates | "128" | **65** (63 active) + 1 added by coord fix = 66 | `missing_coordinates_report.csv` (60 Gandaki, 4 no-province, 1 Bagmati). No geocoding source reachable from sandbox → external dependency |
| Out-of-Nepal coords | 3 | 3 → **0 active** | 7394 East Rapti River: coord (26.295N) contradicts its own district (Chitwan = 27.3–27.7N) → coords cleared (logged, reversible); 6903 Gangkhar Puensum: genuinely a Bhutan/China-border peak → deactivated (reversible); 5880 "3-10": already rejected junk |
| Municipality candidates | 133 | **133 unverified** (of 134 total; 1 csv_import verified), affecting **6,208 destination rows** | `municipality_unresolved.csv` (sorted by affected-record count). Authoritative local-level list not reachable → import workflow exists (`import_municipality_mapping` + admin verification), data dependency remains |

## D. Restaurants / ATMs / essential services — actual status

| Table | Rows | Status |
|---|---|---|
| Restaurant | **0** | Pipeline ready (admin create endpoint + this importer). No legitimate dataset imported yet. |
| OSMEssentialService | **0** | Same. Importer + reports tested with fixtures; awaiting real extract files. |
| Hotel / Hospital / PoliceStation / Destination | 1,653 / 393 / 641 / 8,581 active | unchanged (real curated data) |

**Why still 0:** the only authoritative source reachable in principle is the
Overpass API. Direct HTTPS from this sandbox is blocked at TLS for every
mirror (overpass-api.de, kumi.systems, private.coffee, osm.ch, osm.jp,
lz4, maps.mail.ru — all tested, all fail). The relay path returned real data
3 times, then failed 8 consecutive times with proxy signing errors. Importing
hand-typed samples of the ~40 real ATM records that were returned would not be
nationwide coverage, so they were **not** inserted. This is recorded as the
single largest remaining external data dependency (§J).

## E. Categories — architecture

- `OSMEssentialService.Category` extended 12 → 26 values (migration 0075).
- **Dynamic-category proof**: created a `charging_station` row → appeared in
  `/places/nearby/` and `/places/search/` with **zero code changes**. New
  categories flow through because nearby/search filter by the category field,
  not a hard-coded whitelist.
- Destination-side categories were already database-driven (`Category` model +
  admin CRUD since earlier phases).
- Multi-category places: an OSM element maps to one canonical service category;
  a physical place hosting several services is several OSM elements (the source
  model), each with its own canonical row — no duplicated "place" entity needed.

## F. AI hallucination — tested

| Probe | Result |
|---|---|
| Itinerary for `Xylophonistan` (nonexistent) | **200, itinerary=[], detail="No verified destinations… Nothing was substituted"**. Previously this silently returned a Panchapuri/Surkhet/Jumla plan — **bug found and fixed this phase** (2 regression tests) |
| `ml/itinerary/modify` with "Fake Hotel McFakeface" | 200, nothing persisted (Destination count unchanged, name absent) |
| Any AI path writing authoritative rows | none: AI plans only reference existing Destination IDs (`destination_id` + `slug` on every spot) |

## G. Security spot-checks (this phase)

- `POST /admin/travel-services/create/` anonymous → 401/403 (regression test);
  capability-gated (`restaurants` module, `change`) — the earlier
  false-positive test was corrected in the previous phase.
- Importer is CLI-only (management command): no HTTP surface.

## H. Performance

No bulk import has landed yet, so the previous medians stand (nearby 4 ms,
search 3.6 ms). The importer writes inside a transaction per file and the
search bbox prefilter already indexes `(latitude, longitude)` — re-measure
after the first real import (§J step 5).

## I. What changed in code this phase

| File | Change |
|---|---|
| `tourist/management/commands/import_osm_services.py` | NEW — idempotent OSM importer |
| `tourist/models.py` + migration `0075` | Category choices 12 → 26 |
| `tourist/views_ml.py` | unknown requested place → honest empty plan (no substitution) |
| `tourist/tests_regression.py` | +4 tests (importer idempotency/rejections, categories, unknown-place ×2) |
| `dataset/osm_reports/*.csv/.json` | municipality/missing-coords/duplicate reports + import reports |

## J. Remaining external data dependencies (honest list)

1. **OSM bulk extracts** (ATM/bank/restaurant/cafe/pharmacy/hospital/clinic/
   police/fuel/bus_station/…): source = Overpass area query (procedure in §B).
   Blocked by sandbox network. Steps when reachable: fetch per category →
   `dataset/osm_raw/<cat>.json` → `manage.py import_osm_services` (dry-run
   first) → re-run nationwide audit numbers → re-measure perf.
2. **Authoritative municipality list** (753 local levels): source = MoFALD /
   official Nepal local-level gazette. Workflow exists; mapping must not be guessed.
3. **Geocoding for 66 missing coordinates**: needs a geocoder with Nepal
   coverage; candidates must pass district validation + admin approval.
4. **Trekking route polylines/stages**: no authoritative open dataset fetched;
   trekking today = destination points + road-graph ETAs (labeled "estimated").
   `TREKKING DATA = INCOMPLETE` stands.

## K. Verification this phase

- New/targeted tests: importer (2) + unknown-place (2) + prior admin-create (3)
  + search-intent (2) — all OK.
- Full suite (`tourist` + `audit`): see final turn message for the count.
- e2e live: **77/77**. Frontend build ✓.

## L. Final status

**PARTIALLY READY** — architecture and workflows are complete and tested;
functional behavior is correct and honest (no substitution, no fabrication);
the remaining gap is **bulk real data**, which is an external dependency with a
ready, tested import path — not a code gap.
