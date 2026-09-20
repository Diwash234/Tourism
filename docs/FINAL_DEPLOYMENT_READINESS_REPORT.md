DEPLOYMENT READINESS COMPLETE

Repository: Diwash234/Tourism
Branch: arena/01a07999-tourism
Commit: 9f9d9cd (verified tip after evidence-backed close-out)
Date: 2026-09-20

Backend: Django 5.0.6 + DRF, Python 3.11.2 — `manage.py check`: 0 issues
Frontend: React 18 + Vite — `npm run lint`: 0 errors / 409 pre-existing style warnings (lint now also covers scripts/*.mjs|.cjs; generated nav bundle ignored — DEF-017), `npm run build`: clean, bundle 1.92 MB main chunk (558 KB gz) after DEF-013 code-splitting; AdminDashboard/maps/navigation lazy-loaded
Database: **SQLite is the current, default database** (WAL-hardened, foreign keys ON — verified at runtime: `journal_mode=wal`); PostgreSQL 18.4 verified as the drop-in scale-up path via `DATABASE_URL`

Tests:
Backend: 492/492 OK on SQLite (full `manage.py test` runner, includes SEO/sitemap/health suite) AND 492/492 OK on real PostgreSQL 16.2 (pgserver-provisioned, `PG_DUMP` client env, includes the SEO suite and migration 0072); PostgreSQL 18.4 additionally passed 487/487 at commit `e7d7c7b`
Frontend: lint 0 errors (409 style warnings, pre-existing), production build clean
E2E: 67/67 API-level checks passed against live servers (backend :8000 + vite :5173)
Navigation: `audit_navigable_places` — all 6,597 public destinations navigable with real Nepal coordinates, 5/5 route smoke tests (via corridor-graph fallback, labelled); GPS replay fixtures included in backend suite

Security:
Production config: `validate_production_config` → RESULT: PASS (hardened SQLite accepted, unhardened rejected)
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
- Backend tests (492/492 on both SQLite and PostgreSQL 16.2; 487/487 on PostgreSQL 18.4 at `e7d7c7b`)
- Frontend lint/build
- Security check (0 security warnings) + production config (RESULT: PASS)
- PostgreSQL (real 18.4: migrations, full suite, backup+drill restore)
- Backup/restore drill (SQLite: 19.3 MB sha256-verified archive → 6,669 destinations restored into scratch; PG: pg_dump + SQL drill)
- Data quality (machine-readable report generated; 0 fabrication indicators)
- API E2E (67/67)
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
Application implementation: production-readiness checks passed (492/492 SQLite, 0 security warnings, config validator PASS, data-quality report clean of fabrication). Deployment: GO for a single-node SQLite deployment after the host runs `close_production_gates.sh` green and the launch-day checklist in `docs/DEPLOYMENT_GUIDE.md`; external-service gates (OSRM/weather/OAuth/feeds) and device/browser validation remain pending on real credentials/hardware and must not be reported as LIVE until their providers are exercised.

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
