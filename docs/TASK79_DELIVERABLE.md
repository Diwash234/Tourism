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
| Destination navigation screen | `POST /api/v1/navigation/travel-options/` — per-mode comparison (taxi / bus / walk / bicycle) with routing-service distances; costs from the admin fare card only (labelled estimates; delete a key → "Information unavailable"); rule-based recommendation with reasons; along-the-way recorded places with detour minutes; before-you-go facts from the destination record; OSRM turn-by-turn via `routing_service.route_steps()` when a live provider is configured, honest note otherwise. Rendered by `TravelOptionsPanel` on the Navigation page. |
| Fare card | SiteSetting `fare_card` (migration `0070`) seeds admin-editable typicals (taxi base 100 + 50/km, bicycle rental 200, bus 30) — editable in Django admin (`SiteSetting`) and via the CMS settings JSON editor; values are always labelled as estimates. |
| Itinerary UX (§35) | Save (existing), plus new **Share** (link with `?city=&days=` rebuilds the same plan; Web Share API when available) and **Export / print** buttons. |
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
python manage.py runserver 0.0.0.0:8000

# frontend
cd frontend/Tourism
npm install
npm run dev                         # http://localhost:5173

# checks
python manage.py test tourist.tests_regression --parallel 1
node e2e/live.mjs                   # requires backend on :8000 + frontend on :5173
```

## 18. Test results (this session, latest run)

- Backend: `tourist.tests_regression` — **195 tests OK** (district architecture ×7,
  time-aware plans, travel options ×3, sqlite hardening, itinerary district-specificity ×4, …).
- Live e2e: **60/60 passed**, including district API, travel-options,
  district-specific itineraries, admin→DB→API→public flow, WebSocket chat,
  routing-provider honesty checks.
- Frontend: eslint 0 errors on changed files; production build green.

## 19. Remaining limitations (honest)

1. **Turn-by-turn instructions** require a reachable OSRM-compatible provider
   (admin site setting `routing_provider`). The sandbox cannot reach OSRM, so
   the UI shows the honest note instead; distances/times still come from the
   bundled graph / straight-line estimates, clearly labelled.
2. **District tourism content** grows only from verified sources or admin
   entry by design — many district profiles currently say "Information
   unavailable" for description; that is the intended behaviour (§5/§42).
3. **ML itinerary service** (port 8001) is optional; the DB fallback is the
   verified path in development.
4. **Responsive audit at 320–1440px** was implemented-by-design (drawer,
   grids, footer) but not machine-verified in this sandbox (no headless
   browser available).
5. `bus` timing uses a ×1.6 heuristic over road time and is only offered when
   a fare is configured; real transit schedules are never fabricated.
