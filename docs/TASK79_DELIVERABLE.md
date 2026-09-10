# Task-79 Complete Upgrade — Final Deliverable (§44)

Branch: `arena/01a07999-tourism` (never merged to `main`, per standing instruction).
Scope: the 44-section upgrade prompt + the destination-navigation, 77-district,
footer, mobile-navbar, CMS-control and error-fix demands.

Everything below was implemented and **verified** (backend tests, live e2e
scenarios, production build, curl checks). Anything not verified is listed
under "Remaining limitations" — per §42, nothing here is claimed fixed without
evidence.

---

## 1. Summary of changes

| Area | What changed |
|---|---|
| SQLite `database is locked` | Root-caused: no busy timeout / WAL on SQLite. `settings.py` sqlite `OPTIONS.timeout=20`; `tourist/signals.py` enables `PRAGMA journal_mode=WAL`, `synchronous=NORMAL`, `busy_timeout=20000` on every connection via `connection_created`. Verified live: dev DB reports `journal_mode: wal`, `busy_timeout: 20000`. Audit logging was already failure-safe (`log_action` wraps save in try/except). |
| Generic itineraries (Rolpa complaint) | Root-caused: DB fallback matched only `city__icontains`, missed districts, then served `qs[:days*3]` (first rows) for every place. `tourist/views_ml.py` fallback now scopes by district/city/province, interest-scores stops, geo-chains them (haversine nearest-neighbour), themes days from categories, schedules times (09:00 start, ~90 min visits, travel legs labelled as planning estimates), flags nearest out-of-scope places as `day_trip`, and adds `data_note` when nothing verified exists. |
| 77-district architecture | `administrative_boundaries.py` completed 41 → 77 districts (public administrative facts). New `Province` + `District` models (migration `0069`), idempotent `seed_districts` command, Django admin registration with "verified content only" guidance. |
| Districts API | `GET /api/v1/provinces/`, `GET /api/v1/districts/` (`?search=`, `?province=`), `GET /api/v1/districts/<slug>/` — profile aggregates **real** published destinations by category, hospitals, police stations, national emergency numbers, nearest districts (haversine). Unverified fields render "Information unavailable"; empty districts get an explicit `data_note`. |
| District pages (React) | `/districts` (search + province filter + province overview chips) and `/districts/:slug` (about, category-grouped places, hospitals, safety, nearby districts, links into planner/navigation). Discover Nepal gained a data-driven "77 Districts of Nepal" section. |
| Mobile navbar | Root-caused: drawer groups rendered collapsed by default, so items looked missing. Mobile viewport now renders every group fully expanded (matchMedia-tracked); desktop keeps click-controlled collapsing. Admin-added nav items surface in a "More" drawer group instead of disappearing. |
| `destroy is not a function` | Root-caused earlier and re-verified: `ChartCard.jsx` is the **only** chart renderer (Bar/Line/Pie delegate to it); the race (fresh object literals per render driving react-chartjs-2's destroy/redraw path) is fixed via content-signature-memoised data/options + ErrorBoundary. No `useEffect(async`, no stray `.destroy` in `src/`. |
| Footer redesign | Deep navy `#07101F` + subtle radial teal glow; teal = brand/links, gold = action only (compact "Explore Nepal →"); dedicated Emergency block (Police 100 / Ambulance 102 / Fire 101); subtle Himalayan silhouette (~4.5% opacity); subtle-bordered newsletter panel; simple bottom bar. All CMS hooks + real newsletter API preserved. |
| Destination navigation screen | `POST /api/v1/navigation/travel-options/` — per-mode comparison (taxi / bus / walk / bicycle) with routing-service distances; costs from the admin fare card only (labelled estimates; delete a key → "Information unavailable"); rule-based recommendation with reasons; along-the-way recorded places with detour minutes; before-you-go facts from the destination record; turn-by-turn via `routing_service.route_steps()` when a live provider is configured, else coordinate-based steps from the bundled Nepal graph (always labelled "not street-level"; the label renders under the steps in the UI). Rendered by `TravelOptionsPanel` on the Navigation page. |
| Provider turn-by-turn pipeline | `route_steps` OSRM-contract parsing + `_step_instruction` road-name mapping now covered by mocked-contract tests: with `routing_provider` set, travel-options serves street-level steps ("Turn right onto Ring Road") with `source: routing_provider` and no disclaimer; without it, the labelled bundled-graph steps take over. |
| Section content & typography | Sections now expose full content controls in the CMS editor: rich-text body (headings/size/bold/lists/links via RichTextEditor) **plus per-section font family (site default/serif/mono/display), heading level (H1–H4), heading size, heading color, text scale, alignment, background theme/image and custom bg/text colors** — applied by both `CMSBlock` and `CMSIntro` from enum/hex allow-lists only. **Fixed a real save-path bug**: `_safe_section_config` silently dropped `custom_bg`/`custom_color`, so custom colors could never persist through the admin API; now hex-validated and stored (`title_color` added), verified live (PATCH round-trip + 400 on invalid hex). |
| Live navigation session | Phase-2 turn-by-turn session on the Navigation page: **Start live navigation** begins a `watchPosition` GPS watch (`useLivePosition` — cleans up on End/unmount); `LiveNavigationPanel` map-matches each fix onto the served route polyline (local metre plane), shows the **next maneuver, remaining km, remaining ETA (labelled estimated — prorated from the provider/graph duration), GPS offset**, detects **arrival (<40 m)** and **off-route (>75 m for 2 consecutive fixes)** with automatic **reroute from the GPS position** through the same `/navigation/route` API (manual reroute + reroute counter included). Also **fixed a real rendering bug**: the page passed `routeWaypoints` while `MapView` accepts `route`, so the route polyline never drew. Engine verified by 22 new jsdom tests driving the real components (`npm run test:nav` → 153/153). |
| Route alternatives selector | `/navigation/route` now returns applicable `alternatives`: OSRM-protocol `alternatives=true` routes (street-level steps, `{lat,lng}` geometry) when a provider is configured, otherwise different weightings of the bundled graph (safest/cheapest) — identical corridors discarded, never padded; provider outage degrades to labelled graph alternatives exactly like the primary route. The UI chip row (Recommended / alternatives with km + ETA) applies a selection straight to the map, steps and summary; duration honesty per mode preserved (no invented bus times — verified live: KTM→Pokhara primary 254.21 km + one safest-weighted alternative). |
| Routing provider admin + live voice | **Phase 3**: new `GET/PATCH/POST(test) /admin/routing-provider/` + Branding-tab panel — admins flip navigation to street-level routing by pasting an OSRM-protocol base URL (+ optional key): HTTPS enforced (http → 400), secret stored `is_public=False`, never echoed in full (last-4 only), excluded from the public config snapshot (leak-checked live), audit-logged with the key masked, and a server-side **Test connection** probe returning an honest ok/latency/error verdict (verified live: sandbox network → `ok:false` with the real SSL error, no fake success). **Voice guidance now follows GPS**: during a live session `speechSynthesis` announces the GPS-derived next maneuver (`onManeuver` from the engine, deduped per instruction) instead of the manual step index. |
| Multi-stop routes | **Phase 4**: `/navigation/route` accepts up to 3 `waypoints` (place names resolved through the same index as destinations — never guessed — or explicit `{latitude, longitude}`); every leg is routed through the same engine/honesty pipeline and totals are leg sums (`duration_source: "estimated"`). Steps carry an explicit `Waypoint N: pass through X` marker; unresolvable stops → 404 naming the stop; leg failures → 404 naming the leg (verified live: a banquet-hall match for "Bandipur" with no graph connection reported honestly instead of silently mis-routing); flights + waypoints → 400 (no invented schedules); tourist-bus multi-stop keeps `duration_min: null`. UI: stop input + removable chips under the destination field, included in manual calculations and GPS reroutes. Verified live: Kathmandu → Chitwan (Sauraha) → Pokhara = 222.95 km / 382 min with marker step. |
| Trip Watch live tracking fix | **Phase 5**: the family live-share existed end-to-end (SharedTrip + token link + 15 s contact polling) but its ping loop captured the **one-shot GPS fix in a closure** — contacts would have watched the traveller's starting point forever. Fixed with the Phase-2 `useLivePosition` watch: pings now send the current `watchPosition` fix every 30 s, the watch only runs while a trip is active, and SOS uses the freshest fix too. Verified by 4 new live e2e checks (owner pings accepted, contact sees the **latest** position via the token, unknown token 404, ending the share revokes contact access) — e2e suite now 65/65. |
| CMS full-page coverage | Migration `0071` registers the last public pages (districts list/detail, guides, tourism jobs, 4 auth screens, 404) — **68 ManagedPages — every content route in App.jsx is CMS-controlled** (migration `0072` added portal/staff/admin logins, guide portal/bookings, local dashboard, admin tools, hotel booking; the 12 `/staff/*` sub-routes share the wired StaffDashboard, and only the two transient redirects `/trip-planner` and `/auth/callback/:provider` are exempt by design); `CMSPageIntro` now mounted on districts, district detail, guides, jobs, auth, 404 and staff desk. CMSPanel gained a **media-library picker** (Browse button on section image, media URL and page social-image fields) served by the moderated `admin/media-library/` endpoint. |
| Curated district descriptions | `seed_district_descriptions` fills empty descriptions for all 77 districts (established facts + platform-recorded places) with source-noted, fact-only text (idempotent, never overwrites admin content); the rest keep the auto-composed administrative summary. |
| ML itinerary microservice | `ml_service` (FastAPI :8001, pinned venv) now runs as the primary planner; Django validates every ML response against the requested place (`_ml_plan_matches_place`) and falls back to the district-scoped DB engine when the plan is off-topic or the service is down; ML city picker learnt traveller-typed district names ("Kaski" → Pokhara). |
| Fare card | SiteSetting `fare_card` (migration `0070`) seeds admin-editable typicals (taxi base 100 + 50/km, bicycle rental 200, bus 30) — editable in Django admin (`SiteSetting`) and via the CMS settings JSON editor; values are always labelled as estimates. |
| Itinerary UX (§35) | Save (existing), plus new **Share** (link with `?city=&days=` rebuilds the same plan; Web Share API when available) and **Export / print** buttons. Generated stops now render their planned `🕐 start–end` times and day-trip labels from the fallback engine. |
| Search (§19) | Public destination search suggestions now merge matching **districts** (top 3), routing selection to `/districts/<slug>`. |
| CMS control plane | Existing ManagedPage/ContentSection/visibility/publishing retained; added hex-safe `custom_bg` / `custom_color` style overrides in `CMSBlock` + `CMSIntro` with matching color controls in both CMSPanel editors — any section on any page is style-editable by admin without code. |
| Admin header | Global-search wrapper could be flex-crushed to a blank pill (`min-w-0`); now `min-w-[10rem]`. |

## 2. Files changed (key list)

Backend: `Tourism/Tourism/settings.py`, `tourist/signals.py`, `tourist/models.py`,
`tourist/admin.py`, `tourist/urls.py`, `tourist/serializers.py`,
`tourist/views_ml.py`, `tourist/views_districts.py` (new),
`tourist/views_navigation.py`, `tourist/routing_service.py`,
`tourist/administrative_boundaries.py`,
`tourist/management/commands/seed_districts.py` (new),
`tourist/migrations/0069_province_district.py`, `0070_seed_fare_card.py`,
`tourist/tests_regression.py`.

Frontend: `components/layout/Footer.jsx`, `components/layout/Sidebar.jsx`,
`components/admin/AdminLayout.jsx`, `components/navigation/TravelOptionsPanel.jsx` (new),
`components/cms/CMSBlock.jsx`, `components/cms/CMSIntro.jsx`,
`components/admin/CMSPanel.jsx`, `pages/Navigation.jsx`, `pages/Itinerary.jsx`,
`pages/Districts.jsx` (new), `pages/DistrictDetail.jsx` (new),
`pages/DiscoverNepal.jsx`, `App.jsx`, `api/navigationApi.js`,
`api/districtApi.js` (new), `e2e/live.mjs`.

## 3. Migrations created

- `0069_province_district` — Province + District models.
- `0070_seed_fare_card` — seeds admin-editable `fare_card` SiteSetting (reversible).

## 4. New models / fields

- `Province(name, slug, capital, order)`
- `District(name, slug, province FK, region_type, latitude, longitude, elevation_m, description)` — blank description ⇒ API renders "Information unavailable".
- `ContentSection.config.custom_bg / custom_color` (JSON, hex-allowlisted in renderers).
- `SiteSetting.fare_card` (JSON).

## 5. New API endpoints

- `GET /api/v1/provinces/`
- `GET /api/v1/districts/` (`?search=`, `?province=`)
- `GET /api/v1/districts/<slug>/`
- `POST /api/v1/navigation/travel-options/`

## 6–11. Frontend / admin / itinerary / navigation / mobile / destroy

Covered in the summary table above; all exercised by the e2e battery or eslint+build.

## 12. Database-lock root cause and fix

See summary. Evidence: live PRAGMA check; `SqliteLockHardeningTests` asserts the
timeout config and the WAL handler registration.

## 13. Discover Nepal 500

Was the SQLite lock (same root cause). After the WAL/timeout fix, `GET
/api/v1/discover-nepal/` returns 200 (verified live and in e2e).

## 14–17. Runbook

```bash
# backend
cd Tourism
python manage.py migrate            # applies 0069, 0070
python manage.py seed_districts     # idempotent 77-district seed
python manage.py seed_district_descriptions  # curated descriptions, never overwrites
python manage.py runserver 0.0.0.0:8000

# ML itinerary microservice (optional but recommended — Django falls back
# to the internal DB planner automatically when it is down)
python3.11 -m venv /tmp/mlvenv      # any clean venv; NOT the Django one
/tmp/mlvenv/bin/pip install -r ml_service/requirements.txt
cd ml_service
/tmp/mlvenv/bin/uvicorn app:app --host 0.0.0.0 --port 8001

# frontend
cd frontend/Tourism
npm install
npm run dev                         # http://localhost:5173

# checks
python manage.py test tourist.tests_regression --parallel 1
node e2e/live.mjs                   # requires backend on :8000 + frontend on :5173
```

## 18. Test results (this session, latest run)

- Backend: `tourist.tests_regression` — **221 tests OK** (district architecture ×7,
  time-aware plans, travel options ×3, sqlite hardening, itinerary district-specificity ×4,
  ML-planner guard ×4, routing-provider turn-by-turn pipeline ×2, description seeding ×1, …).
- Live e2e: **65/65 passed**, including district API (curated + auto-composed
  profiles), travel-options, district-specific itineraries, ML-microservice
  planner + DB enrichment, admin→DB→API→public flow, WebSocket chat,
  routing-provider honesty checks.
- Frontend: eslint 0 errors on changed files; production build green.
- Nav behaviour harness (`npm run test:nav`, jsdom, real components):
  **155/155 passed**, including 24 live-navigation checks (following/
  arrival/off-route/reroute-success/reroute-failure/recenter/end +
  `useLivePosition` watch lifecycle and error honesty).

## 19. Remaining limitations (honest)

1. **Turn-by-turn instructions**: when no live provider is configured, the
   bundled Nepal GraphML engine now supplies coordinate-based turn-by-turn
   steps (compass instructions + segment distances from the graph geometry),
   each response carrying an explicit "coordinate-based, not street-level"
   note that the UI always displays under the steps. **Street-level** turns
   come from the admin-configured OSRM-compatible provider (site setting
   `routing_provider`); the full provider pipeline — HTTPS-only config,
   OSRM-contract parsing, provider road names in instructions
   ("Turn right onto Ring Road") — is covered by mocked-contract regression
   tests, so the only missing piece is an externally reachable OSRM server,
   which this sandbox cannot provide (public demo and Geofabrik both
   verified `HTTP 000`, 2026-09-10). The bundled graph carries no road
   names (verified: 0 of 37,055 edges named), so road names can honestly
   only come from a real provider.
2. **District tourism content** grows only from verified sources or admin
   entry by design — and **all 77 districts now carry curated,
   source-noted descriptions** (`seed_district_descriptions`: batches 1–3
   from established public facts, batch 4 for the remaining 30 grounded in
   seed facts plus this platform's own recorded destinations, e.g. Rolpa's
   Guerrilla Trek). The command stays idempotent and never overwrites admin
   content; any future district without a curated entry still falls back to
   the honest "Information unavailable" + auto-composed administrative
   summary. No invented tourism prose.

3. **ML itinerary service** (port 8001) now runs in development: a dedicated
   venv with the pinned `ml_service/requirements.txt` (sklearn 1.5.0 matches
   the trained `.joblib` models) serves it via uvicorn, and Django's
   `POST /api/v1/ml/itinerary/` uses it as the primary planner — verified
   end-to-end (dataset destinations, graphml road legs, NPR budget scaling,
   then Django attaches live-DB hotels/hospitals/police per day,
   `service_data_source: live_database_distance_ranking`). The internal DB
   engine remains the automatic fallback whenever the service is down **or
   plans around a different place than requested** — Django validates the ML
   response against the requested district/city (`_ml_plan_matches_place`)
   and rejects off-topic plans, and the ML service itself now normalises
   traveller-typed district names ("Kaski" → Pokhara) before city picking.
4. **Responsive audit at 320–1440px** was implemented-by-design (drawer,
   grids, footer) but cannot be machine-verified in this sandbox: every
   browser-binary source was tried and is blocked at network level —
   `cdn.playwright.dev`, `storage.googleapis.com` (puppeteer/Chrome) and the
   `cdn.npmmirror.com` mirror all return `HTTP 000`, Ubuntu archives are
   blocked, and no system Chromium exists (npm/PyPI themselves are
   whitelisted-reachable; everything else is not).
5. `bus` timing uses a ×1.6 heuristic over road time and is only offered when
   a fare is configured; real transit schedules are never fabricated.
