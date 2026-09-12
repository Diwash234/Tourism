# Nationwide Verification & Data Completion Report — 2026-09-12

Repo: Diwash234/Tourism · branch `arena/01a07999-tourism` · HEAD `bb10f99` (pushed)
All numbers below were regenerated from the live database/API this session — none reused from older reports.

## A. Repository & service state
- Services: Django :8000, ML :8001, Vite :5173 all live; migrations applied, tree clean.
- Commits this arc: `f3b43b8` OSM importer (validate/normalize/apply) → `25812ae` district fallback + audit fixes → `f8caa18` nationwide itinerary + search hygiene → `b7022b9` research-fabrication close + nav substitution fix → `ffde703` canonical IDs on itinerary stops + district normalization → `5256260` hospital bulk import → `bb10f99` provenance report.

## B. Tests (this session)
- Django full suite: **506/506 OK** (reg30). ML pytest: **10/10**. Frontend E2E: **77/77**. Production build: ✓ (11.9s).

## C. Real OSM import status
- Pipeline: `import_osm_services` (validate → bbox/Nepal check → nearest-district ≤80 km → `osm_id` canonical → report). Now accepts both full Overpass JSON and NDJSON relay files.
- **This session's real batches: 250 Nepal hospitals + 250 Nepal pharmacies** (Overpass `area ISO3166-1=NP`, `out skel center 250` per category, osm_base 2026-09-12T06:42:51Z / 06:51:02Z). Each: created / 0 rejected; **idempotent rerun: 0 created, 250 duplicate** (IDs stable). DB now holds **500 OSM service rows, 0 auto-verified** (admin queue).
- Every row: `osm_id` = node/<id>, `source_url` to the OSM element, `is_verified=False` until admin verification. Names pending enrichment (skel output carries no tags) — honest placeholder labels, never invented names.
- Network limitation: sandbox has no direct internet; Overpass reachable only via the page-relay (non-deterministic proxy). Remaining categories (pharmacies, ATMs=1,122 known, police, transport) follow the same resumable batch pattern.

## D. Coverage (live DB — see coverage_matrix.json)
| Province | Districts | Destinations | Hotels* | Attractions | Hospitals (OSM) |
|---|---|---|---|---|---|
| Koshi | 14 | 1,133 | 130 | 398 | via OSM service table |
| Madhesh | 8 | 190 | 44 | 121 | " |
| Bagmati | 13 | 2,997 | 1,072 | 858 | " |
| Gandaki | 11 | 2,819 | 1,141 | 610 | " |
| Lumbini | 12 | 736 | 319 | 239 | " |
| Karnali | 10 | 501 | 151 | 261 | " |
| Sudurpashchim | 9 | 205 | 56 | 110 | " |
*hotels = category contains "hotel"; guest houses/hostels counted separately.

- Districts with **zero destinations (official names)**: Eastern Rukum, Parasi, Western Rukum — all alias artifacts of the 2018 renames (rows exist under "Rukum" (11) and "Nawalparasi West" (13)). Not verified absence of places.
- District-string hygiene: provinces carry many alias/variant strings (e.g., Koshi 41 distinct strings vs 14 official districts). Fixed this session: "Nawalparasi W" → "Nawalparasi West" (6 rows, IDs preserved).
- Quality queue (live counts): **67 destinations missing coordinates** (admin UNRESOLVED_GEOGRAPHY mechanism; no silent assignment), **131 missing category**, **133 unresolved municipality mappings / 1 verified** (unresolved by design — no authoritative source consumed yet, no guessing).

## E. Municipality mapping
Authoritative-source pipeline + `MunicipalityMapping` (source/date/raw/normalized/verified) in place; 133 candidates stay **unresolved** until an authoritative gazetteer (e.g., MoFAGA list) is imported.

## F–G. Search & nearby (7-province live battery — seven_province_verification.json)
- Every province: real DB record travels DB → API → search → destination → nearby → itinerary → navigation with **canonical IDs at each stage**; nearest-neighbour distances verified against recomputed haversine (errors ~0.0000 km), not just HTTP 200.
- Scope-leak regression tests (12/12) + live negative probes: fake province "Gondwanaland", fake district "Northern Wakandapur", fake place "Quandangle Bristlemoor" → **count 0** in every province.

## H. Itinerary
- All 7 provinces generate ≥2-day plans; every stop now carries `destination_id` + `canonical_source` (`verified_database` when matched; `ml_suggested_unverified` when not) — regression-tested (`ItineraryCanonicalIdTests`). District fallback for 73 districts; ML path audited fallback-free (unknown districts honestly return "no plan").

## I. Navigation
- Routes derive from DB records only; this session **removed the nearest-destination silent substitution** → unknown places return 404 `UNRESOLVED_DESTINATION`; assumed Pokhara origin now flagged `origin_assumed: true` (compat list endpoint documented exception). Regression-tested. No hard-coded coordinate fallbacks remain in the active path.

## J. Admin
- OSM services visible in admin (archive/verify, never hard-delete); dedupe = exact-evidence merge with rollback, name-only duplicates never auto-merged; geography issues queued, not auto-fixed.

## K. AI trust model
- Tiers: authoritative/manual > verified external > OSM imported > AI suggested > unverified > rejected (`audit.SourceTier`).
- **Research-endpoint fabrication pipeline closed** (`b7022b9`): unknown place → pending stub (no coords, no municipality, no marketing copy, invisible in public search); real place → existing record. AI never auto-becomes authoritative.

## L. Trekking
- **Implemented this session**: `TrekkingRoute` + `TrekkingStage` models (migration 0076: stages, waypoints/coords, elevation gain/loss, distance, difficulty, duration, season, permits, accommodation, safety, provenance, verification state) and the `import_trekking` pipeline (dry-run default, idempotent on slug, imports never self-verify, out-of-Nepal coords nulled not clamped) — regression-tested (`TrekkingImportTrustTests`).
- **TREKKING DATA DEPENDENCY = EXTERNAL AUTHORITATIVE SOURCE REQUIRED** (e.g., Nepal Tourism Board/TAAN trails): the DB contains **0 routes** — pipeline ready, no coverage claimed. Road routing ≠ trekking; the road navigation engine never serves these.

## M. Gaps (classified)
1. **Missing external data**: remaining OSM batches (hospitals/pharmacies beyond first 250 each; ATMs=1,122 known, police, transport — relay-limited, resumable); municipality gazetteer; trekking trails dataset.
2. **Database**: 67 missing coords; 131 missing categories; 3 districts reachable only via alias; district-string alias sprawl; hospital names pending tag enrichment.
3. **Network limitation**: no direct sandbox internet; relay proxy non-deterministic (batches are resumable).
4. **Code**: none known open — every audit finding this session was fixed + regression-tested.

## N–O. Verdicts
- **System architecture & data integrity: READY** (validation gates, provenance, trust tiers, no fabrication paths).
- **Functional core (7 provinces): READY** — end-to-end verified with canonical IDs, negatives clean.
- **Data coverage: PARTIALLY READY** — attractions/hotels broad; services just started (250 hospitals); mappings/geography queue open.
- **Trekking data: NOT READY** (external dependency).
- **OVERALL: PARTIALLY READY — trending READY** (was PARTIALLY READY with open fabrication risk; that risk is now closed and tested).
