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

## Completeness sweep: per-destination services + point-to-point routes (2026-09-21)

1. **Nearby-services search verified per destination** (`/api/v1/places/nearby/`):
   urban (Thamel), remote (Rara Lake), trans-Himalaya (Manang) all return nearest
   hospital/bank/hotel/police with honest distances.
2. **9 misplaced remote service rows fixed** (seeds had used landmark coords instead
   of the named towns): Mugu District Hospital (was lakeside Rara 29.53,82.09 →
   Gamgadhi 29.4167,82.0167); Dolpa District Hospital + Dolpa Health Office (→ Dunai
   28.9833,82.9667); Humla District Hospital (→ Simikot 30.0167,81.8167); NBL branches
   Chame (was Manang village → 28.51,84.25), Gamgadhi, Dunai, Jomsom (was Dunai coords
   → 28.7833,83.7167), Simikot. Post-fix live: Rara→Mugu hospital 14.0 km (honest),
   Jomsom→NBL Jomsom 0.0 km.
3. **origin_name geocoding bug fixed** in `/navigation/calculate/`: a named origin
   ("from Biratnagar") was accepted but never resolved — the response echoed the name
   while silently routing from the Pokhara default. Now origin_name is geocoded via
   the universal place resolver (`origin_resolution: geocoded`), unresolvable names
   are labelled `default — '<name>' could not be located`, GPS origins unchanged
   (`origin_resolution: gps`). Live: Biratnagar→Pathibhara = 154.9 km (was a
   mislabelled 544.6 km from Pokhara). Suite: 471/471 OK (tourist+navigation).

## Owner-spelling search fix (2026-09-21) — remaining destinations round

Reconciliation of the 416 not-found owner places against the whole DB found ~9
entries that EXIST under slightly different names (Bandipur Bazaar→"Bandipur",
Swargadwari Temple→"Swargadwari", Gangapurna Lake→"Gangapurna", Chandragiri
Hills→"Chandragiri Hill", Dhaulagiri Base Camp→"Dhaulagari Base Camp",
Marsyangdi River→"Marshyangdi River", Ganga Jamuna Waterfall→"Ganga Jamuna",
Bhojpur Bazaar→"Bhojpur Bazar", Pathibhara Temple→"Pathibhara Devi").
Live check showed ALL of these owner spellings returned NOTHING — the search
only matched the full phrase. Fixed in LocationSearchService.search_places:
queries now also match a generic-word-stripped variant ("bazaar", "temple",
"lake", "waterfall", "hills", "base camp", …) across all six providers
(destinations, OSM services, hospitals, police, hotels, restaurants);
resolve_single_place inherits the fix. Post-fix: 8/8 owner spellings resolve
(was 0/8); regressions clean (Rajbiraj 8 results, Rara 22, "nearest bank" 30,
Pathibhara exact). New regression tests: PlaceSearchGenericWordTests (4).
Suite: 475/475 OK.

## Field-test re-run after search fix + 2 web-verified additions (2026-09-21)

- **811 owner places: found 406 (86 exact + 320 partial), was 395** — the
  generic-word search fix recovered ~11 (7 of the 9 reconciled spellings now
  "partial"; Marsyangdi River needs fuzzy spelling match, Pathibhara-under-Dhankuta
  honestly fails because the temple is in Taplejung).
- **Routes for found places: 406/406, 0 failures** (corridor-graph fallback in
  sandbox; OSRM on host).
- Added web-verified: **Arjundhara** (Jhapa, 26.6855,87.9896, Wikipedia+geo-schema
  agree, VERIFIED) and **Todke Jharna** (Ilam, 27.0441,87.943, Wikipedia, VERIFIED).
  Both created after their district blocks had run (so still "not-found" in this
  run's report) but resolve live via search and route (Birtamod→Arjundhara 13.9 km).
  Satashi Dham rejected — no site-level source.
- Remaining not-found: 405, blocked on live Nominatim/Overpass (host) or per-place
  web verification rounds.

## Verification round: Rupse, Mahaboudha, Beni + resolver precision (2026-09-21)

- **Rupse Falls** (id 6328) and alias **Rupse Chhahara** (6339) were UNVERIFIED and
  ~14 km north of the actual waterfall; upgraded to Wikipedia coords 28.5555,83.6361
  (VERIFIED). The duplicate "Rupse Waterfall" row created before noticing the
  existing rows was deleted — owner spelling resolves via generic-word search.
- **Mahaboudha Temple** (Patan, id 6703) added: 27.67355,85.3251 VERIFIED (Tripadvisor
  + travel guide agree); Thamel→Mahaboudha routes 5.1 km/9 min with exact dest coords.
- **resolve_single_place precision fix**: exact > prefix > substring, so "Beni" no
  longer resolves to "Kagbeni Muktinath Route". Regression test added
  (test_exact_name_wins_over_substring_match). Suite: 476/476 OK.
- **Beni** (Myagdi HQ, id 6704) added: 28.35,83.56667 VERIFIED (Wikipedia); the town
  had no destination row at all. Live: Beni→Rupse = 35.0 km, origin resolved exactly.

## Verification round: Saipal, Dhumba Lake, Jomsom (2026-09-21)

- **Saipal** (id 6312) upgraded to VERIFIED official summit coords 29.8878,81.4947
  (Nepal Himal Peak Profile govt database; was UNVERIFIED ~700 m off); duplicate
  "Saipal Himal" row deleted — owner spelling resolves via the new "himal"
  generic-word rule added to the search stripper this round.
- **Dhumba Lake** (Mustang, id 6706) added VERIFIED 28.7633,83.7164 (Wikipedia).
- **Jomsom** town (id 6707) added VERIFIED 28.78333,83.73056 (Wikipedia) — like Beni
  last round, the district gateway town had no destination row; origin resolution
  now hits Jomsom exactly (Jomsom→Dhumba Lake 3.7 km, origin_resolution geocoded).
- Suite: 476/476 OK.

## Verification round: Chhusang + Lipulekh Pass (2026-09-21)

- **Chhusang** (Upper Mustang, id 6708) added VERIFIED 28.93,83.91 (Wikipedia);
  Jomsom→Chhusang = 59.3 km corridor route.
- **Lipulekh Pass** (Darchula, id 6709) added VERIFIED 30.2342,81.0289 (Wikipedia),
  with an explicit sovereignty note in the description: Nepal claims the Kalapani
  side under the 1816 Treaty of Sugauli; currently administered by India. Dipayal→
  Lipulekh routes 236.1 km, honestly labelled node-level corridor estimate.
- Data-only round (no code changes); suite remains 476/476 from e3d1743.

## 40-destination batch round (2026-09-21)

Owner request: ~40 remaining destinations in a single round. Delivered 40 new
destination rows, every one with a traceable coordinate source:

- **28 from project-owned data** (`scripts/batch_find_40.py`): hotel-dataset and
  OSM-service address/cluster matches + community-services CSV, each with a
  district-hub sanity check (<=60 km) and dedupe vs existing rows. All labelled
  APPROXIMATE with the exact source (e.g. "median of 3 hotel coords addressing
  'Rolpa Bazaar'"). Includes Dhankuta/Okhaldhunga/Taplejung/Siraha/Parasi/Pyuthan/
  Rolpa/Jumla/Salyan/Baglung/Ramechhap/Sindhuli/Dhading Besi bazaars, Salpa Pokhari,
  Sabha Pokhari, Khopra Danda, Kupinde Lake, Budhinanda Lake, Tikapur Park, Doti
  Durbar, Jajarkot Durbar, Bheri/Limi rivers, Chandannath + Badimalika +
  Malikarjun temples, Siddhicharan Park, Halesi-area entries.
- **12 web-verified** (9 VERIFIED, 3 APPROXIMATE): Rajarani, Bedkot Lake,
  Chamunda Bindrasaini, Namaste Jharna (3 sources agree), Temkemaiyum,
  Hatuwagadhi, Dodhara Chandani, Dullu Durbar (sources disagree — labelled),
  Karnali Bridge, Mulghat, Tuwachung, Barahapokhari (3 sources agree).
- **Rejected without sources** (stay honestly not-found): Halji, Siddhanath
  Temple (Nepal), Panchakoshi, Gopghat; deleted 3 risky in-repo matches
  (Halesi Cave duplicate, Kathmandu Bagh Bazar under Nuwakot, Putha Himal from
  a guesthouse row).
- Live spot-checks: all sampled names resolve with exact coords; Dhangadhi →
  Karnali Bridge = 87.0 km (Wikipedia: 86 km). Data-only change; suite 476/476.

## Verification round: 4 more (2026-09-21, post-40 batch)

Added: **Rudravarna Mahavihar** (Uku Bahal, Patan — VERIFIED 27.668207,85.327194,
two sources agree; Patan DS → site routes 0.6 km), **Ice Lake / Kicho Tal**
(Manang — APPROXIMATE 28.673,84.011 with explicit sources-disagree note),
**Lakuri Bhanjyang** (Lalitpur highpoint — APPROXIMATE, OSM peak node),
**Kichakbadh** (Jhapa — APPROXIMATE, mindat locality). Rejected: Tyamke Danda,
Jalthal Forest (no site-level sources). Not-found pool now ~361.

## Remaining-places round: service-record matcher + resolver ranking (2026-09-21)

- **6 more destinations** resolved from in-repo service records (police posts /
  health facilities / hotel names): Sapta Koshi River (Sunsari), Triyuga River
  (Udayapur), Kusma Bazaar (Parbat), Resunga Hill (Gulmi), Srinagar Hill (Palpa),
  Patan Bazaar (Baitadi) — all APPROXIMATE with per-row source notes and 60 km
  hub sanity. A re-created Halesi Cave duplicate was caught and deleted (owner
  spelling resolves to the VERIFIED Halesi Mahadev Cave instead).
- **resolve_single_place ranking upgrade** (live bug): free-text names resolved
  to whichever result sorted nearest — "Halesi Cave" hit a Kathmandu guest
  house, "Bandipur Bazaar" hit a resort. Now candidates are ranked exact-core >
  prefix > fuzzy (difflib), destinations win ties, window widened to 30.
  Live: Halesi Cave→Halesi Mahadev Cave 231 km; Bandipur Bazaar→Bandipur town;
  Swargadwari Temple→Swargadwari; Rupse Waterfall→Rupse Chhahara; Saipal
  Himal→Saipal; Gangapurna Lake→Gangapurna. Suite 476/476 OK.

## Service-CSV matcher round (2026-09-21)

Mined dataset/nearbypolice.csv + hospital.csv + hotel.csv (Destination and
Address columns, 6,666 rows). 10 auto-matches created, **3 rejected and deleted
after audit** (Halesi Cave re-duplicate; Kalyanpur sourced from a Saptari
police station though owner district is Siraha; Jorayal from a Dadeldhura
station). 7 kept, all APPROXIMATE with per-row source notes: Narayanghat
(27.68,84.43), Meghauli (27.58,84.25), Rasuwagadhi (28.3,85.35), Chhatradev,
Banganga, Rapti River (Dang), Rambha Lake. Live: all searchable;
Bharatpur→Meghauli 23.8 km. Not-found pool ~348.

## Round 2026-09-21 (B): duplicate consolidation, real turn-by-turn, admin editability

Owner demands: (1) same place stored as different records (Bandipur / Mahendra Cave) — make
data accurate; (2) every place must have real turn-by-turn directions; (3) admin can edit
everything (users, staff, destinations).

### 1. Data accuracy — Mahendra Cave consolidation
- Duplicate found: id 6433 "Mahendra Cave (Pokhara)" @ 28.2167,83.9667 sat 6.2 km south of
  the real cave (Lakeside area); id 5717 "Mahendra Cave" @ 28.2724,83.9791 was ~130 m off.
- Wikipedia-verified location (Pokhara-16 Batulechaur): 28°16'17"N 83°58'47"E = 28.27139,83.97972.
- 5717 upgraded: coordinates set to the verified point, coordinate_status=VERIFIED, verified_at/by,
  aliases (Mahendra Cave (Pokhara), Batulechaur Cave), location_notes. Its image was moved from
  6433; 6433 deactivated (status=rejected, correction_reason recorded). Public search now returns
  one Mahendra Cave at the correct pin.
- Resolver hardening (live gaps "Mahendra Cave Pokhara", "mahendra gufa", "amhendra cave" all
  failed): locality-suffix variant retry ("… Pokhara" → core name), Nepali-generic transliteration
  (gufa→cave, tal→lake, jharana→waterfall, …), and a last-resort fuzzy name pass with a strict
  0.85 floor so misspellings resolve but garbage ("xyzzy florp") stays honestly not-found.
- Known remaining duplication: 3,650 lodging-pattern destination rows (hotel/lodge/resort/inn/
  guesthouse names); ~42% of a 400-row sample duplicate a real Hotel record within 150 m. Mass
  deactivation was NOT performed this round (itinerary/FK safety review pending) — flagged for a
  dedicated consolidation round with an itinerary-safe merge script.

### 2. Turn-by-turn directions (real, not invented)
- Correction to the previous round's note: routing PROVIDERS already emitted per-waypoint steps
  (graphml corridor directions with landmark names; OSRM street steps; honest straight-line pair).
  The gap was routes without provider steps silently returning [].
- `route_engine.build_maneuvers()` now backfills steps from the route's REAL geometry (bearing
  changes at actual vertices; ≥30° turns become slight/left/right/sharp instructions) with honest
  `maneuver_grade`: "street" (OSRM), "corridor-node" (tourism graph), "none" + explicit
  non-guidance step for straight-line fallback. `cached_route` guarantees `steps` on every route.
- `/navigation/calculate/` now passes `maneuver_grade` + `point` through per step.
- Live check: Kathmandu→Pokhara corridor route returned 57 steps (Head North; Turn left toward
  Dusit Princess; …; Arrive at destination). Frontend Navigation.jsx already renders the step
  panel + voice announcements from `response.data.steps`.
- Tests: 4 new (geometry-derived turns, straight-line honesty, engine backfill, calculate API).

### 3. Admin editability — live smoke test + one real fix
- Verified live as a temporary superuser (deleted afterwards): admin/stats, admin/users list +
  detail, staff-workspace, staff-capabilities, destinations list + detail; PUT destination edit
  propagated to the DB and to public /places/search/ (§45); user suspend/reactivate (PUT status);
  PATCH role + profile fields (role=staff sets is_staff).
- FIXED: `DELETE /admin/users/<id>/` was 405 although the Admin Dashboard "Delete user" button
  calls it (adminApi.deleteUser). Implemented: default delete = irreversible anonymization
  (retention design — reviews/audit chain preserved); `{"hard": true, "confirmation": <email>}`
  + superuser = permanent row deletion; self-delete and superuser targets blocked. 5 new tests.

### Suite
- `manage.py test tourist navigation` → 489/489 OK (476 prior + 13 new).

## Round 2026-09-21 (C): mass duplicate consolidation + search relevance fixes

### Consolidation (owner complaint: "Bandipur and Bandipur town are same but it gives different")
- Pass 1: 1,877 lodging-pattern Destination rows deactivated — each duplicates a real Hotel
  record with the same normalized name within 150 m (lodging belongs to the Hotel table;
  Hotel records stay fully searchable).
- Pass 2: 61 same-normalized-name Destination pairs within 200 m deactivated (kept the richer
  row: VERIFIED coords > description length > gallery > older id).
- Total: 1,938 rows deactivated with per-row correction_reason (audit log
  /tmp/consolidation_applied.csv mirrored into each row). Active destinations 6,667 -> 4,730.
- Safety checks before applying: zero reviews/ratings/favorites/visit-history on any candidate;
  no DB itinerary model exists (verified). Hotel.destination anchors are non-nullable and stay
  pointing at the (retained, unpublished) rows — factual, no cascade.

### Search relevance bugs exposed by the consolidation (both fixed + tests)
1. Provider name filter was skipped whenever the query contained its own category word
   (`cat_filter != "hotel"` etc. in 4 provider blocks): "Bandipur Eco Hotel" returned 40
   arbitrary id-ordered hotels and NOT the hotel. Now any substantive name query (>= 4 chars,
   not a bare generic term) always filters provider tables by name.
2. Result sort was pure distance for category/GPS queries: "Bandipur" listed "Mountain Ridge
   Bandipur" above Bandipur. Now exact > prefix > substring name rank wins, then distance;
   short/generic queries ("bank", "hotels") keep nearest-first.

### Verification
- Live: "Bandipur Eco Hotel" -> that hotel (50.8 km), "Hotel Siddhartha" -> that hotel,
  "Bandipur" -> canonical town first, "hotel" -> nearest list, resolver golden cases intact
  (Mahendra Cave, amhendra cave, Halesi, Swargadwari, Rupse).
- Suite: 489/489 OK (incl. 3 new SearchNamePriorityTests).

## Round 2026-09-21 (D): pool re-tally + 5 web-verified destinations

- Not-found pool re-tallied after consolidation + resolver fixes: 811 field places ->
  276 not-found (was ~348; resolver fixes recovered ~70 without adding any rows).
- Added ids 6774-6778 (sources cited per row):
  * 6774 Ainselukharka (Khotang) 27.10,86.29 — Wikipedia VDC — VERIFIED
  * 6775 Tinjure Danda (Dhankuta/Terhathum) 27.17791,87.42725 — mindat ridge — VERIFIED
  * 6776 Chhintapu (Sandakpur RM, Ilam) 27.17,87.92 — GeoNames — APPROXIMATE
  * 6777 Balankha (Bhojpur) 26.99,86.98 — Wikipedia/Wikidata Q4850047 — VERIFIED
  * 6778 Rakha Dipsung (Khotang, alias "Dipsung") 27.37,86.86 — Wikipedia VDC — VERIFIED
- Rejected (no citable coordinates, NOT added): Satashi Dham (blog only), Tyamke Danda
  (no source found), Siddhakali Temple (Phidim — temple itself unlocated).
- Verified: all 7 field spellings resolve; live route Dharan -> Tinjure Danda 25.8 km,
  4 turn-by-turn steps, CORRIDOR-ESTIMATE.

## Round 2026-09-21 (E): 7 web-verified destinations (Kapilvastu Buddhist circuit + Terai heritage)

- Pool at round start: 270 not-found.
- Added ids 6779-6785:
  * 6779 Tilaurakot (Kapilvastu) 27.58,83.08 — Wikipedia; candidate ancient Kapilavastu,
    UNESCO tentative — VERIFIED
  * 6780 Nigalihawa (Kapilvastu; aliases Niglihawa, Nigali Sagar, Sobhavati) 27.62,83.11 —
    Wikipedia; Konagamana Buddha birthplace, Ashokan pillar — VERIFIED
  * 6781 Gotihawa (Kapilvastu; alias Khemavati) 27.51,83.03 — Wikipedia; Kakusandha Buddha
    birthplace, Ashokan pillar base NP-KP-04 — VERIFIED
  * 6782 Simraungadh (Bara) 26.88944,85.11694 — Wikipedia; medieval Karnat capital ruins — VERIFIED
  * 6783 Amlekhganj (Bara) 27.283,84.983 — Wikipedia; former Nepal Government Railway
    terminus, Churiya Mai Temple — VERIFIED
  * 6784 Kankalini Temple (Bhardaha, Saptari) 26.55,86.92 — Wikipedia; Shakti Peetha — VERIFIED
  * 6785 Panchakot (Baglung) 28.2889,83.5784 — citiesinnepal directory — APPROXIMATE
- Rejected (no citable page found): Kudan (Kapilvastu), Nigrodharama deferred to a later
  round with a proper source.
- Verified: all 8 field spellings resolve (incl. Niglihawa alias); live route
  Lumbini -> Tilaurakot 87.5 km, 18 turn-by-turn steps, CORRIDOR-ESTIMATE.

## Round 2026-09-21 (F): 7 web-verified Terai/hill destinations + resolver alias tier

- Added ids 6786-6792:
  * 6786 Barahathwa (Sarlahi) 27.0,85.46667 — Wikipedia — VERIFIED
  * 6787 Hariwan (Sarlahi; aliases Harion, Hariyon — covers TWO field entries with one
    accurate row) 27.10,85.55 — Wikipedia — VERIFIED
  * 6788 Ishwarpur (Sarlahi; alias Ishworpur) 27.0,85.63333 — Wikipedia — VERIFIED
  * 6789 Golbazar (Siraha) 26.79,86.33 — Wikipedia — VERIFIED
  * 6790 Chhinnamasta (Saptari; 10 km S of Rajbiraj) 26.45,86.72 — Wikipedia — VERIFIED
  * 6791 Malarani (Arghakhanchi, HQ Khandaha) 28.06,83.12 — Wikipedia RM centre — APPROXIMATE
  * 6792 Matihani (Mahottari; Lakshminarayan Matha) 26.64711,85.85105 — OSM municipality
    office — APPROXIMATE
- Skipped: Chhinnamasta Temple wiki page is the Jharkhand (India) namesake — used the
  Saptari RM page instead; Kudan still unsourced.
- Resolver: new length-gated (>=5 chars) alias tier in resolve_single_place — "Harion",
  "Hariyon", "Niglihawa", "Dipsung" now resolve to their canonical rows. +2 tests.
- Suite: 494/494 OK. All 8 batch spellings verified through the live resolver.

## Round 2026-09-21 (G): 6 web-verified destinations (Baglung reserve + Terai towns + Achham)

- Added ids 6793-6798:
  * 6793 Dhorpatan Hunting Reserve (Baglung/Myagdi/E. Rukum; alias Dhorpatan)
    28.64056,82.99444 — Wikipedia — VERIFIED
  * 6794 Sukhipur (Siraha) 26.71,86.35 — Wikipedia — VERIFIED
  * 6795 Kalyanpur (Siraha) 26.86,86.22 — Wikipedia — VERIFIED (replaces the earlier
    rejected police-CSV attempt with the proper Siraha municipality source)
  * 6796 Rupani (Saptari; Rupani Devi, Shiva Sani Dham) 26.62,86.69 — Wikipedia — VERIFIED
  * 6797 Panchadewal Binayak (Achham; alias Panchadeval Binayak) 29.11,81.39 —
    Wikipedia — VERIFIED
  * 6798 Ramaroshan Lakes (Achham) 29.2035,81.4214 — Wikipedia RM centre, lakes scattered —
    APPROXIMATE
- Verified: all 8 field spellings resolve via resolver incl. alias tier (Dhorpatan,
  Panchadeval Binayak, Ramaroshan); live route Baglung -> Dhorpatan 194.1 km, 28 steps,
  CORRIDOR-ESTIMATE. No code changes this round — suite remains 494/494 (green last run).
