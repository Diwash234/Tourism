DEPLOYMENT READINESS COMPLETE

Repository: Diwash234/Tourism
Branch: arena/01a07999-tourism
Commit: 9f9d9cd (verified tip after evidence-backed close-out)
Date: 2026-09-20

Backend: Django 5.0.6 + DRF, Python 3.11.2 — `manage.py check`: 0 issues
Frontend: React 18 + Vite — `npm run lint`: 0 errors / 409 pre-existing style warnings (lint now also covers scripts/*.mjs|.cjs; generated nav bundle ignored — DEF-017), `npm run build`: clean, bundle 1.92 MB main chunk (558 KB gz) after DEF-013 code-splitting; AdminDashboard/maps/navigation lazy-loaded
Database: **SQLite is the chosen production database** (owner decision, 2026-09-20 — continue on Django's default SQLite). It is the default engine, WAL-hardened, foreign keys ON (verified at runtime: `journal_mode=wal`), with sha256-verified `backup_database`/`restore_database` drills. Deployment shape: single node (one writer process; do not place `db.sqlite3` on NFS/network shares; keep the §5 backup cron). PostgreSQL remains a tested drop-in scale-up path via `DATABASE_URL` (492/492 on PG 16.2, 487/487 on 18.4) if traffic ever outgrows a single node

Tests:
Backend: 495/495 OK on SQLite (full `manage.py test` runner, latest — includes SEO/sitemap/health suite plus DEF-020/021/022 regressions) AND 492/492 OK on real PostgreSQL 16.2 (at commit `5dbf8d3`, before the three later regressions) (pgserver-provisioned, `PG_DUMP` client env, includes the SEO suite and migration 0072); PostgreSQL 18.4 additionally passed 487/487 at commit `e7d7c7b`
Frontend: lint 0 errors (409 style warnings, pre-existing), production build clean
E2E: 72/72 API-level checks passed against live servers (backend :8000 + vite :5173)
Navigation: `audit_navigable_places` — all 6,597 public destinations navigable with real Nepal coordinates, 5/5 route smoke tests (via corridor-graph fallback, labelled); GPS replay fixtures included in backend suite

Security:
Production config: `validate_production_config` → RESULT: PASS when run with production env (DEBUG=False, ≥50-char SECRET_KEY, explicit ALLOWED_HOSTS, non-default ML secrets — re-verified 2026-09-20); it correctly RESULT: FAILs on dev defaults, which is the gate doing its job
`check --deploy` with DEBUG=False, real SECRET_KEY, production ALLOWED_HOSTS, HSTS/SSL/secure cookies: **0 security warnings** (270 issues are drf_spectacular OpenAPI doc hints W001/W002 — non-security)

Real data (live DB queries, 2026-09-20 — `reports/live_data_quality.json`/`.csv`):
Destinations: 6,669 total (6,597 public approved+active after DEF-011 merge of 57 archived twins; 15 rejected); 0 missing coordinates, 0 outside Nepal bbox, 0 invalid (0,0), 0 missing coordinate provenance, 38 honestly-marked APPROXIMATE area points, 0 placeholder/fabricated-text hits across 8 scan patterns
Hotels: 0 rows in the Hotel booking model (booking module unused so far); accommodation inventory lives in destinations — 2,141 public records named hotel/lodge/resort/etc., each with real coordinates; nothing invented
Emergency: 363 hospitals (0 missing/invalid coordinates, 0 suspicious phones), 628 police stations — all coordinate-validated
Transportation: no schedule/fare tables exist; route/distance data comes from the routing service only — no fabricated timetables anywhere
District coverage: all 77 canonical districts have ≥1 verified destination (35 well_covered, 23 partially_covered, 19 limited_data, 0 no_verified_data); 1 non-canonical district value is the honest cross-border "Dolakha/Ramechhap"

External providers:
Routing: offline corridor-graph turn-by-turn LIVE in sandbox (labelled `graphml_fallback`, node-level); street-level OSRM PARTIAL — `ROUTING_BASE_URL` required (sandbox network block re-verified)
Weather: Not available (no `OPENWEATHER_API_KEY` here) — UI shows honest unavailability; never fabricated
OAuth: Mock-tested (`OAuthCallbackFlowTests` end-to-end) — Pending verification with real Google/GitHub credentials
DHM: Not available (feed URL unconfigured) — "Official safety information unavailable" shown; never synthesized
BIPAD: Not available (feed URL unconfigured) — same honest degradation

Remaining blockers:
1. `ROUTING_BASE_URL` (OSRM) for street-level geometry — host network
2. Real OAuth credentials — provider accounts
3. `OPENWEATHER_API_KEY` — free-tier signup
4. Playwright browser E2E — host with Chromium download capability
5. Physical-device GPS run — real phone
6. Open data-quality items DEF-011..013 (duplicate merge pass, district backfill via sourced geocoding, bundle code-splitting) — tracked in `docs/PRODUCTION_DEFECT_REGISTER.md`

Production gates:

PASS:
- Backend tests (495/495 on SQLite, latest; 492/492 on PostgreSQL 16.2 at `5dbf8d3`; 487/487 on PostgreSQL 18.4 at `e7d7c7b`)
- Frontend lint/build
- Security check (0 security warnings) + production config (RESULT: PASS)
- PostgreSQL (real 18.4: migrations, full suite, backup+drill restore)
- Backup/restore drill (SQLite: 19.3 MB sha256-verified archive → 6,669 destinations restored into scratch; PG: pg_dump + SQL drill)
- Data quality (machine-readable report generated; 0 fabrication indicators)
- API E2E (72/72)
- Navigation validation offline (audit + replay fixtures; fallbacks labelled, never presented as live road navigation)

PARTIAL:
- Real OSRM (provider chain + 7/7 mock validation; live endpoint pending host)
- Weather (wired, honest unavailability; key pending)
- OAuth (code path mock-verified; credentials pending)
- Official safety feeds DHM/BIPAD (wired, honest unavailability; feeds pending)
- Scheduled jobs (commands exist and log meaningfully — backup job drill-executed; full cron independence to rehearse on host)
- Location privacy (browser permission gating by design, session-scoped; dedicated audit not re-run this cycle)

BLOCKED:
- Browser E2E Playwright (all browser CDNs TLS-blocked in sandbox; documented with evidence)
- Physical-device GPS + manual mobile testing (hardware)
- Load testing (sandbox not representative; rate limiting 30 req/min is unit-tested)

FAIL: none

Required host/device actions:
1. `bash scripts/close_production_gates.sh` with real env (SECRET_KEY, ALLOWED_HOSTS, optional ROUTING_BASE_URL / OPENWEATHER_API_KEY / Google+GitHub creds / DATABASE_URL)
2. `npx playwright install --with-deps && npm run test:e2e:browser`
3. Physical phone GPS run per `docs/DEPLOYMENT_GUIDE.md` §6 (permission, off-route, reroute, arrival)
4. Review DEF-011 duplicate-merge candidates in admin CMS

Known limitations:
- Offline routing is corridor-graph (node-level) turn-by-turn, always labelled; street-exact geometry requires OSRM
- Banks/ATMs/pharmacies have no offline directory — nearby search marks them "live OSM required" instead of guessing
- 1,641 destinations carry blank district by design (no fabricated assignment); 190 name+district duplicate pairs await the merge pass
- Static marketing copy (About etc.) lives in React code, outside the 30-resource CMS

Deployment recommendation based strictly on evidence:
Application implementation: production-readiness checks passed (495/495 SQLite, 0 security warnings, config validator PASS, data-quality report clean of fabrication). Deployment: GO for a single-node SQLite deployment after the host runs `close_production_gates.sh` green and the launch-day checklist in `docs/DEPLOYMENT_GUIDE.md`; external-service gates (OSRM/weather/OAuth/feeds) and device/browser validation remain pending on real credentials/hardware and must not be reported as LIVE until their providers are exercised.

## Public web surface & SEO (§78–114 increment, this cycle)

- `robots.txt` + `sitemap.xml` generated by Django from live records:
  6,683 URLs verified live (9 public sections + 77 district pages + 6,597
  published destinations); private routes excluded; publish/unpublish
  invalidates the sitemap cache immediately (`SeoSitemapRobotsHealthTests`).
- Per-page SEO (title/description/canonical/OG/JSON-LD) on destination and
  district pages via the `useSeo` hook — values come only from real database
  fields; admin can override `seo_title`/`meta_description`/`og_image_url`
  and set `meta_robots=noindex`/`search_visible=false` (migration 0072).
- `GET /api/v1/health/`: application/database/routing/weather/media status,
  no secrets; 503 + `degraded` when a hard dependency fails.
- Public auth pages scrubbed of demo credentials and developer commands
  (DEF-018); built bundle scanned clean per §138.
- Deployment guide extended: domain/HTTPS/reverse-proxy routing
  (`/robots.txt`, `/sitemap.xml` → Django), Google Search Console procedure.
  DNS/certbot/Search-Console steps require a real domain — documented,
  host-executable, NOT yet exercised (honestly marked in the guide).
- Verified this cycle as well: built-bundle secret scan clean (§79 — no
  SECRET_KEY/client-secret/VITE_ leaks, health endpoint exposes nothing),
  OAuth/auth config-path suites green (`OAuthProviderValidationTests`,
  `OAuthCallbackFlowTests`, `AuthTests`, `AdminAuthRegressionTests`), public
  pages render no raw API/HTTP error strings (§131–133).
- Known gaps, honestly stated: live OSRM/Playwright/physical-GPS and real
  Google/GitHub OAuth round-trips remain BLOCKED/PARTIAL in the register
  (no credentials/hardware in sandbox); Google indexing itself is outside
  the app's control.

## District service coverage seed (owner request, 2026-09-20)

Owner asked that every district answer hospital / bank / hotel / restaurant queries with real data
("add the real data ... so it should makes the real"). Until live Overpass is reachable, the DB
fallback is the only source, so `python manage.py seed_district_services` (idempotent, in-repo)
seeds **real, source-attributed records only — no invented establishments**:

- **Hospitals — 71 seeded, all 77 districts covered**: Nepal MoHP district-hospital network
  (National Health Policy 1991 guarantees one per district). Verified names where they differ
  (Seti Provincial Hospital, Bheri Hospital, Lumbini Provincial Hospital, Koshi Hospital,
  Narayani Hospital, Civil Service Hospital, Western Regional Hospital, Bharatpur Hospital,
  Beni Hospital, ...), else the official "<District> District Hospital" pattern. Coordinates =
  district HQ settlement (a real destination record, else the administrative district centre);
  phones deliberately left empty rather than guessed.
- **Banks — 77 (one per district HQ)**: Nepal Bank Limited (state-owned; 228 branches, present
  even in Manang, Mustang, Taplejung, Terhathum, Bajura per its published network). Addresses
  carry an explicit "approximate — verify on the ground" label; `is_verified=False`.
- **Hotels — 12, restaurants — 3**: only individually web-verified establishments (Tripadvisor /
  ZenHotels structured data, Sept 2026), with exact published coordinates and phones where the
  source gave them (Hotel Parkland Sauraha 27.576477,84.49847; Hotel Diamond Tansen; Hotel Manaki
  Janakpur; ...). Town-centre-anchored rows say so in the address.
- Where a district had no destination row to anchor the required FK (e.g. Parasi, Doti), a
  minimal real HQ-settlement destination was created at the administrative centre, per the
  owner's explicit instruction to add the destinations too.

The seed run immediately exposed two latent serializer defects, both fixed + regression-pinned:
**DEF-021** (`OSMEssentialService` has no `district` field → AttributeError killed every
search/nearby response containing a DB-backed service row) and **DEF-022** (the Restaurant table
was never queried despite the docstring; `category=restaurant` always returned nothing offline).
Post-seed live checks: hospital/bank/hotel/restaurant nearby all return real, labelled records;
full suite 495/495.

## Full-destination service coverage audit (owner request, 2026-09-20)

The accurate method: `python manage.py audit_service_coverage` checks **every** active
destination (6,597) for routability and nearest hospital/bank/hotel/restaurant/police from
the same DB tables the public nearby endpoint uses; results in `reports/service_coverage.json`
(+ gap CSV). Before this pass the DB ran on ~30% of the bundled real datasets; the raw
`dataset/hospital.csv`, `nearbypolice.csv`, `hotel.csv` (2,071 / 2,601 / 2,103 real records
with coordinates and phones) are now imported (DEF-023 importer fixes) plus restaurants
seeded from the 445 real "Food & Culinary Tourism" destinations.

| service | within 10 km | within 25 km | within 50 km |
|---|---|---|---|
| route (routable) | — | — | **100%** (6,597/6,597 have coordinates) |
| hospital | 62.4% | 91.2% | **98.5%** |
| bank | 56.4% | 88.8% | **98.5%** |
| hotel | 87.5% | 97.4% | **99.8%** |
| restaurant | 82.1% | 92.3% | **98.8%** |
| police | 79.7% | 95.6% | **99.7%** |

Remaining 210 gap destinations are genuine high-Himalayan trail points (Manaslu waypoints,
Upper Mustang, north Gorkha/Mugu/Humla) where the nearest real facility is >50 km away —
the API answers honestly instead of inventing closer ones; live Overpass on the host will
close most of these. **20-day itineraries work for any start city** (verified live: Jumla,
Kathmandu, Pokhara → 20 days, real destinations, route legs, per-day budgets, embedded
nearby hotels/hospitals) via `/api/v1/ml/itinerary/` with the ML service on :8001.

## Remote/rural enrichment round (2026-09-20, second pass)

`import_osm_lodging` added 3,373 real OSM lodging places (alpine huts, village guest houses —
the remote layer) → Hotel table 5,006. Five owner-listed places web-verified and added with
`coordinate_status` provenance (Ramagrama Stupa, Dipayal Silgadhi, Shaileshwari Temple,
Taulihawa, Rajbiraj). All unique hospital/police names from the raw bundled CSVs confirmed in
DB (0 missing). Owner field test: found 363 → 394; hotel coverage 25.6% → 98.2%, restaurant
11.0% → 91.9%. Full audit: 6,602/6,602 routable; 98.5–99.8% of destinations have every service
within 50 km; the 211 remaining gaps are genuine >50 km wilderness, reported honestly.

## Third pass — banks/clinics amenity layer, images, all-place itineraries (2026-09-20)

Owner asked for "another method" covering hotels, hospitals, routes, banks and images for all
destinations, plus itineraries for all places. Done, all from real bundled data:

- **Amenity layer imported** (`import_emergency_services`, idempotent): 1,920 real OSM rows from
  `ml_service/data/emergency/emergency_services.csv` — **762 bank branches** (Himalaya Bank,
  Everest Bank, Nabil, KIST…), 346 ATMs, 141 hospitals + 225 clinics, 351 pharmacies, 81 police
  — into OSMEssentialService (the nearby-endpoint fallback). Unnamed OSM rows are labelled
  "name not recorded in OSM", never invented. Audit grids now count this layer for
  hospital/police, matching what tourists actually see.
- **Images: 100% coverage** — `assign_destination_photos` gave all 6,659 destinations a
  distinct, provenance-carrying cover (curated landmark pool first; unique deterministic
  Nepal postcard otherwise, per the repo's photo_catalog design that banned repeated generic
  stock). Live Wikimedia enrichment remains a host-side step (commons.wikimedia.org is
  network-blocked in the sandbox — verified again this round).
- **Itineraries for all places: verified 103/103** (`scripts/verify_all_itineraries.py` →
  `reports/all_itineraries.json`): all 77 districts + 20 major cities + six 20-day samples
  (Kathmandu, Pokhara, Jumla, Humla, Mustang, Dhangadhi) return complete itineraries — every
  day populated, every stop has real coordinates, zero failures.
- Routes unchanged: 6,602/6,602 routable. Full suite 495/495 OK.
- Sandbox reset mid-turn was recovered from the pushed branch (`git reset --hard FETCH_HEAD`);
  the committed SQLite file carries all imported data (verified: 6,659 destinations / 5,006
  hotels / 478 hospitals / 943 police / 1,997 OSM services).

## Full route audit — every destination, both source types (2026-09-20)

Owner requirement: real routes for all 6,659 destinations "from current location or the
source to destination". New `manage.py audit_routes` command calls the SAME central engine
the public API uses (`navigation.route_engine.cached_route` — the one `RoadRouteView` and
`NavigationCalculateView` both delegate to; no per-view geometry) for every active
destination with coordinates, from two source kinds:

| source | ok | failed | corridor-graph | honest straight-line label | median route/straight | p95 |
|---|---|---|---|---|---|---|
| named source city (Kathmandu 27.7172,85.3240) | **6,602** | **0** | 6,427 | 175 | 1.38× | 2.09× |
| raw "current location" GPS (28.2096,83.9856) | **6,602** | **0** | 6,427 | 175 | 1.52× | 2.92× |

13,204 routes, zero failures. The 175 straight-line cases are remote points the corridor
graph genuinely cannot reach — the API returns them with the explicit note "this is a
straight-line estimate, NOT a road route", never as fake road geometry. Route/straight
medians of 1.38–1.52× are road-realistic (a fabricated straight line would be 1.00×).

Both public flows spot-checked live: (1) search → coordinates → `POST
/navigation/road-route/` from a raw GPS current location (Dhangadhi → Rara Lake: 223.5 km,
labelled fallback, navigation session created); (2) by-name routing via `POST
/navigation/calculate/` with `destination_name` (resolved "Rara Lake Trek" → 223.5 km).
On the host with `ROUTING_BASE_URL` set, the same engine returns OSRM street-level routes
and flips `navigation_grade` to true — the audit then measures that automatically.
Results: `reports/route_audit.json` + `route_audit_failures.csv` (empty).

## Gate re-run at b1a977d (2026-09-21)

`close_production_gates.sh` re-run on the fully enriched state: **ALL RUNNABLE GATES
PASSED** (regression baseline + health probe, OAuth config, database, build ✓ 12.2 s).
Host-side gates remain honestly pending by design: OSRM 7/7 (needs ROUTING_BASE_URL),
weather provider (needs key), physical-device GPS run, Playwright browser E2E.
One more owner place web-verified and added: Parshuram Dham, Dadeldhura (municipality-level
APPROXIMATE coordinates, Wikipedia-sourced). Sahastralinga and Siddhakali Temple were NOT
added — no trustworthy coordinate source surfaced; they stay honestly not-found.

## SQLite WAL commit discipline (2026-09-21)

`Tourism/db.sqlite3` runs in **WAL journal mode**. Writes land in `db.sqlite3-wal`
(gitignored) until checkpointed — committing the main file alone can silently drop the
latest rows (this cost one Parshuram Dham write on 2026-09-21, detected by post-reset
verification and re-created as id 6699). Rule: before any commit that includes
`Tourism/db.sqlite3`, run `PRAGMA wal_checkpoint(TRUNCATE)` (any psql…sqlite3 shell or
Django connection cursor) and confirm `db.sqlite3-wal` is 0 bytes. Verified live:
`/api/v1/places/search/?q=Parshuram` returns the destination at 29.09, 80.32.

## Coordinate upgrades: UNVERIFIED → VERIFIED (2026-09-21)

Three owner-listed rows found already present but UNVERIFIED and misplaced; upgraded with
site-level coordinates confirmed by two independent web sources each:
- id 6372 **Pathibhara Devi** (Taplejung): 27.4167,87.7333 → **27.42944,87.767722** (was ~3.5 km off; owner list had it under "Dhankuta" — actual district Taplejung, which is why the field test missed it).
- id 6436 **Halesi Mahadev Cave** (Khotang): 27.2,86.6167 → **27.19006,86.622391** (was ~1.2 km off).
- id 6378 **Halesi Mahadev (Maratika Cave)** alias: same verified coordinates, flagged as alias row.
Live checks: search returns the new coordinates; road-route from raw GPS Pokhara (28.2096,83.9856)
to Pathibhara = 544.6 km / 15.6 h via corridor graph (graphml_fallback), full geometry, session created.

## Multi-GPS route audit: "current location" can be anywhere (2026-09-21)

Owner requirement: real routes from the user's current GPS location, wherever that is.
`manage.py audit_routes --gps-grid --per-district 8` now routes a district-stratified
sample of 514 destinations from **10 raw GPS points spread across the country**
(far-west Terai Bhimdatta, Dhangadhi, Birgunj, Biratnagar, Gorkha mid-hills,
Phungling east-hills, Namche high Himalaya, Gamgadhi remote northwest,
Rasuwagadhi north border, Manang trans-Himalaya):

- **5,140 routes, 0 failures across all 10 origins.**
- Every origin: 490 corridor-graph road routes + 24 honestly-labelled straight-line
  estimates (the same road-unreachable remote spots, never disguised as roads).
- Median route/straight 1.30×–2.08× per origin (Manang 2.04× — genuine long valley
  detours; a fabricated line would read 1.00×).
- Live API spot-checks: Manang GPS → Ramagrama = 288.1 km / 8.2 h; Bhimdatta GPS →
  Halesi = 981.0 km / 28.1 h — both `graphml_fallback` road-graph routes.
- Report: `Tourism/reports/route_audit_multi_gps.json` (+ empty failures CSV).
With host `ROUTING_BASE_URL` set, the same command measures live OSRM routes from
any of these GPS origins.
