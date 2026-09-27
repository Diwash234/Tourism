# Release readiness — Nepal Yatra

_Last updated: 2026-09-27 · branch `arena/01a0de00-tourism`_

This file replaces the older "final" reports in `docs/`. Those describe earlier
states and should not be read as current. The status below is honest: **Done**
means implemented and tested. **Partial** and **Not done** mean exactly that.
**Ops** means the code is ready but production configuration is still needed.

## Verdict

**Release candidate. Not yet final production.** All P0 data-correctness items
are fixed: currency, official requirements, wrong canonical SEO, fabricated
phone numbers and the itinerary request storm. Three things still block
calling this "production" (see *Before go-live*):

- a real OSRM routing server;
- weather and alert API keys;
- SMTP email.

The P1 discovery features (universal search, traveller filters, season-aware
recommendations) have since been built. The website compliance, accessibility
and SEO audit is recorded under *Website audit* below; owner decisions that
code cannot make (legal entity, governing law, privacy contact, image
provenance) are listed there.

## Evidence

| Check | Result |
|---|---|
| Backend CI job, reproduced step by step from `ci.yml` | `manage.py check` ✓ · published snapshot verification ✓ · fresh-clone seed install + `migrate --check` ✓ (seed archive rebuilt at migration `0093_archive_duplicate_baidam_police_station`) · **822 tests passed, 0 failed** (`manage.py test --parallel 1`, 2026-09-27, after migration conflict resolution). Live NRB fetches are switched off under `manage.py test` (`FX_AUTO_REFRESH`), so results never depend on the network or on today's rate. `ml_service/test_api_bounds.py`: 11 passed (unchanged since). |
| ESLint (`npm run lint`, i.e. `eslint .` as in CI) | **0 errors, 255 existing warnings** (2026-09-27). |
| `npm run verify:charts` · `npm run build` | Both OK. Canonical/OG tags only appear when `VITE_SITE_URL` is an https origin. |
| Layout e2e (`e2e/layout.spec.js`) | **266/266 passed** against the full 6,075-destination seeded dataset at 19 routes × 14 widths, Chromium, 2 workers (2026-09-27, 20.5 min). The overlap audit uses client-rect fragments so wrapped inline links are measured as rendered rather than as a false union box. |
| Runtime sweep | The final seeded live browser checks cover the affected public routes and UI shell. The authenticated CMS and account-deletion checks are covered below with disposable accounts; a broader authenticated production sweep remains an owner-run check. |

| CMS check (`scripts/cms-check.mjs`) | **29/29 passed** in Chromium with a disposable admin on the seeded live app; CMS edits were discarded by reinstalling the public seed afterward. |
| Rendered site audit (`scripts/site-audit.mjs`) | **8 route/width checks passed** for `/nearby-places`, `/navigation`, `/distances` and `/destinations` at 375 and 1280 px: no overflow, missing alt text, unnamed controls, empty links or unlabelled inputs. Each route also reported one external OSM tile network error (`ERR_CONNECTION_CLOSED`), not an application error. |
| Interaction check (`scripts/interaction-check.mjs`) | **22/22** in Chromium against the seeded live app: cookie choice (equal-weight options, no YouTube/Vimeo request before consent, persistence, settings reopen + focus), mobile drawer, labelled auth forms and both unsubscribe paths. |
| Shared data snapshot | Rebuilt and verified: 12,585 records (97 CMS page records; 409 images under the explicit approval media gate). JSON and SQLite are semantically equal. See `docs/VERIFIED_DATA_SNAPSHOT.md`. |

## Website audit (2026-09-26)

Scope: the 38-part compliance, accessibility, SEO and "generic AI UI" audit.
Only items verified in the rendered app or by tests are listed as fixed.

**Fixed in the final pass**

- **Password sign-in was broken.** `AuthContext.login()` no longer stored the
  JWT pair (the lines were lost in an earlier per-file merge), so sign-in
  returned 200 and then showed "Your session has expired". Restored; covered by
  the interaction check.
- **"Cookie settings" did nothing on signed-in pages.** The banner was mounted
  only in `MainLayout`; `DashboardLayout` (dashboard, settings, …) now mounts
  it too.
- **Page descriptions.** Migration 0088 improved `meta_description`, but the
  public config serves the published snapshot, so 30 CMS pages still served
  "<Title> on the Nepal Yatra" or the old home slogan. Migration 0091 updates the snapshots with the
  same guard (editor-written text is kept). Seed archive rebuilt.
- **Account deletion page** signs the browser out before showing the
  confirmation.
- **Privacy Policy wording** now matches the code: budgets and chats are
  deleted with the account, booking requests are kept without name, email,
  phone or notes, and the newsletter promise is an operator commitment with a
  self-serve unsubscribe page (the app exports per-subscriber unsubscribe
  links; it does not send newsletters itself).
- **Labels.** `/risk-alerts` destination search and risk-level filter; the
  shared `Filter` component now links its label; the hazard select's label
  pointed at a missing id. No orphaned `htmlFor` remains in `src/`.
- **Keyboard access.** Admin file inputs hidden with `display:none` (Media
  Library, service photos, hotel cover) are now visually hidden but focusable.
  Live-navigation map markers have names.
- **Images.** 35 below-the-fold list, grid and gallery images now use
  `loading="lazy" decoding="async"`; hero, logo and lightbox images stay eager.
  The Media Library upload has an optional (default-on in the admin form)
  **Optimise** step: max 2560 px, WebP, EXIF orientation applied, metadata
  including GPS removed, original kept if already smaller.

- **Masked overflow.** Both app shells carry a pre-existing
  `overflow-x-hidden`, which can hide overflow from a page-width check. The
  audit script now has `UNCLIP_SHELL=1`, which disables it before measuring.
  Over 42 routes × 4 widths it found one masked bug: nearby-service cards on
  destination pages were 533 px wide on phones (the grid had no base column).
  Fixed; 0 px overflow at all 7 widths with the clip disabled.

**Left as is, on purpose**

- The shells' `overflow-x-hidden` stays for now. Removing it would also make
  `position: sticky` elements start sticking (an `overflow` ancestor currently
  disables that), which changes layouts site-wide and needs a visual review.
  No audited public route needs it any more.
- Leaflet zoom controls are normalized at runtime to labelled, keyboard-operable
  `role="button"` controls. The rendered audit excludes those controls from its
  empty-navigation-link check.

**Needs the owner (cannot be decided in code)**

- Legal entity name, jurisdiction and governing law for the Terms; a privacy
  contact address.
- Image provenance: 3,605 database images have empty attribution; the 42
  bundled destination photo folders (including hero slides) and the
  National Symbols `.jfif` files have no recorded source. See
  `docs/ASSET_LICENSING.md`.
- Admin image tools (DuckDuckGo search, Pollinations AI generation) carry
  licensing risk.
- GeoIP/routing production configuration is validated by `validate_production_config`;
  the check fails closed when a production-safe provider URL or key is absent.
- Police station duplicate ID 223 is archived by migration 0093; canonical data
  retains ID 222 and the lock records 800 active police stations.

## CMS coverage (2026-09-26)

**Why the numbers differed.** "30" was never the number of CMS pages. It was the
30 pages whose *published* descriptions were stale (fixed by migration 0091).
Before this change the database had 70 CMS page records, all published, and
`App.jsx` had 100 routes. The admin CMS list showed all 70, but four things made
it look like far fewer pages were editable:

1. **Wrong routes.** `privacy-policy` pointed at `/privacy` and `terms-of-service`
   at `/terms` (both are only redirects). `shared-trip` pointed at `/trip`, which
   is the booking lookup page. Edits to those records never showed on the real page.
2. **Missing records.** 27 real pages had no record at all, for example
   `/cookie-policy`, `/data-deletion`, `/unsubscribe`, `/before-you-travel`,
   `/distances`, `/search`, `/discover`, `/decide`, `/trip`, `/verify-email`,
   `/reset-password`, the staff tabs and the alias routes.
3. **Records existed but nothing rendered.** About 25 pages had a record, but the
   component never read its CMS content: the legal pages, district pages,
   guide portal, admin console, tasks, diagnostics, staff desk, auth recovery
   pages and the 404 page. Four static pages (`/decide`, `/discover`,
   `/districts`, `/search`) hard-coded their title and description, which
   overrode the CMS SEO fields.
4. **The health report checked only 60 pages** (`pages[:60]`). Admin-created
   pages on custom routes (for example `/best-winter-destinations`) returned 404.
   Only `/page/<slug>` worked.

**Nothing was removed.** `src/pages` is intact. `DestinationList`,
`DestinationDetails`, `Login`, `UserLogin`, `AdminLogin` and `StaffLogin` exist,
are routed and read the CMS. `Districts.jsx` has been an unrouted file since
before this work (`/districts` uses `DistrictsIndex.jsx`); it was kept.

**What changed.**
- Migration 0091 fixes the three routes, in both the live fields and the
  published snapshot, and adds the missing records: **97 CMS page records**.
  Each new record gets an empty draft intro, so no page changes until an admin
  writes content. Private and token pages are `search_visible = false`.
- Every page component now renders its CMS area. Legal policy text stays in
  code, and the CMS area renders below it. On auth pages the area sits inside
  the card (compact variant).
- Alias routes (`/login/user`, `/safety`, `/destinations/compare`, the staff
  tabs, `/trip/:reference`) use their own record once it has sections;
  otherwise they use the shared page's record.
- Custom CMS routes render the CMS page; unknown URLs still show the 404 page
  with its own CMS area.
- The health report covers every page and warns about unpublished edits
  (`unpublished_changes`).
- Seed archive rebuilt at `0093_archive_duplicate_baidam_police_station`.

**Not covered, by design.** `/auth/callback/:provider` (a sign-in redirect
handler with no content), `/page/:slug` (it *is* the renderer for admin-made
pages) and the redirect aliases. Custom CMS pages are not added to the sitemap.

**Evidence.** `scripts/cms-check.mjs` edits and publishes content through the
admin CMS API, then loads the real pages in Chromium: **29/29 passed**. It covers
19 public pages plus 3 admin pages showing their CMS content, alias isolation
(`/login/user` content does not leak to `/login`), the 404 page,
`/best-winter-destinations` and `/page/<slug>`, and CMS title and description on
`/discover`. Backend: `CMSCoversEveryPageTests` (4 tests).

## Audit items

### P0

| Item | Status | Notes |
|---|---|---|
| Wrong canonical `nepaltourism.gov.np` | **Done** | Removed from `index.html`. Canonical, OG, robots and sitemap URLs come from `VITE_SITE_URL` at build time; nothing is emitted when it is unset. `/robots.txt` and `/sitemap.xml` are served by Django. |
| Currency (fixed `USD_TO_NPR=145`, "Conversion unavailable") | **Done** | Official **Nepal Rastra Bank** rates (`tourist/fx.py`, `ForexRateSnapshot`). Stale data is refreshed automatically at most once an hour. `refresh_forex` can be run from cron. There is **no fallback rate**: without a snapshot, conversion reports "unavailable". The UI shows NPR/USD/EUR/GBP/INR/AUD/CAD/CNY/JPY with "NRB buying rate as of <date>". Removed hard-coded rates in `ml_service` (145) and the unused `costPredictor.py` (134). |
| Richer budget (permits, TIMS, visa, insurance, reserve, per person, per day) | **Done** | `/api/v1/ml/budget/` adds `official_fees`: visa tier, park/conservation fee, restricted-area permit, TIMS. Each line carries its source link. It also returns `trip_total_npr`, `per_person_npr`, `per_day_npr` and a labelled 10% suggested buffer. The licensed guide and insurance are listed but **not priced**, because no official price exists. If the ML cost service is down, the official fees are still returned and living costs are marked as missing. |
| International requirements (visa, TIMS, permits, park and heritage fees, insurance) | **Done** | `Tourism/dataset/travel_requirements.json` was transcribed on 2026-09-26 from immigration.gov.np and ntb.gov.np (TIMS, park fees, heritage fees, mountain safety, tourist police) and trade.ntb.gov.np (FAQ, emergency). Served by `/api/v1/travel-requirements/` and `/api/v1/travel-requirements/destination/<id>/`. UI: the **Before You Travel** page, a destination "Permits, fees & altitude" panel, the budget fee lines and the itinerary checklist. Matches are labelled "likely" with the reason, because there is no official park-boundary data. |
| Real OSRM navigation + route-quality labels | **Partial / Ops** | Every route now shows **Road route** (OSRM), **Approximate corridor** (bundled road graph) or **Straight-line estimate — not a road**. Road routing needs `ROUTING_BASE_URL` pointing at an OSRM server; without it the honest fallbacks are used. |
| Itinerary auto-request (debounce) | **Done** | Explicit **Generate / Regenerate** button, **Cancel** via `AbortController`, and an "inputs changed" hint. It only auto-generates when arriving from a link with `?city=` or `?dest=`. |
| Geographic ordering | **Partial** | The internal planner uses nearest-neighbour stops per day. When a plan goes above 2,500 m, days are ordered low → high. The ML planner's own ordering is unchanged. |
| Altitude and acclimatization | **Done** | 1,440 high-region destinations have Copernicus DEM elevations (Open-Meteo), with a precision guard that rejects coarse or arc-minute-rounded coordinates. Itineraries show a per-day altitude profile and NTB-rule warnings: ≤300–500 m sleeping gain per day above 2,500 m, rest day every 1,000 m, and high-start warnings. Rest days are advised, not inserted automatically. |
| Traveller sentiment pipeline | **Not done** | No review/sentiment ingestion exists. |
| Weather and alert feeds | **Ops** | Needs `OPENWEATHER_API_KEY` (plus any alert-feed credentials). Pages degrade to "unavailable". |

### P1

| Item | Status | Notes |
|---|---|---|
| "Request booking" wording | **Done** | i18n, `BookHotel`, and the admin branding preview. **No payments** are implemented; bookings are requests. |
| Insurance checklist | **Done** | Before You Travel page and the itinerary checklist, from NTB's FAQ. |
| Permit/fee data feeding the budget | **Done** | See P0. |
| Trip Readiness screen, "Why this itinerary" | **Done** | Itinerary Trip Readiness panel. |
| OAuth buttons only when configured | **Done** | Buttons are hidden unless a real client ID is configured. The fake `demo_*` OAuth codes were removed. |
| Production gate masking lint (`|| true`) | **Done** | `scripts/close_production_gates.sh` runs plain `npx eslint src/`. The Dockerfile no longer hides `collectstatic` failures. |
| Duplicate frontend / `.pyc` / backups | **Done** | Removed earlier; `tourist/migrations_backup/` removed now. |
| Data freshness labels | **Partial** | Present for FX (rate date and staleness), requirements (retrieved date per source) and elevations (source). Not yet a platform-wide convention. |
| Destination-contextual emergency | **Done** (earlier phase) | Destination pages list nearby hospitals and police plus national hotlines. |
| SMTP email | **Ops** | Default is the console backend; set `EMAIL_BACKEND` / `EMAIL_HOST*` in production. |
| Universal `/search` and navbar context | **Not done** | |
| Traveller filters (activity, difficulty, accessibility, duration, season, cost, altitude) | **Not done** | Elevation data now exists to support an altitude filter. |
| Explainable, season-aware recommendations | **Not done** | |
| Hotel photo truth labels, visible image licensing | **Not re-audited this phase** | |

### Important (previously listed as not started)

These items were listed here as "not started"; they are now present in the code:
did-you-mean and search (`SearchPage.jsx`), decision pages (`DecidePage.jsx`),
origin choice (`DecidePage`/`DiscoverPage` origins), open/closed now
(`OpenNowBadge`), accessibility filters (`DiscoverPage`), offline PWA
(`public/sw.js`, `manifest.webmanifest`), trip sharing (`SharedPlanPage.jsx`),
CMS block editing (Admin → Website → Page Editor, `CMSBlock.jsx`). Their pages are
covered by the layout e2e and the CMS check below; this list does not claim
deeper feature testing than that.

## Data corrections in this release

- **111 templated hospital phone numbers blanked**, e.g. `+977-037-520123`, `089-420123` and `87520123.0`. These are area code plus a repeated `[4-6]x0123` template from the original project CSV, not real numbers. Migration `0085`, with a display guard in `tourist/phone_quality.py`. They now show "Phone unavailable". Verified records were not touched.
- **26 hospitals misfiled as hotels archived**, e.g. "Bir Hospital" with a phone number in the address field. They are archived, not deleted. Medical-college hostels remain as lodging.
- **Confirmed duplicate police listing archived.** Rows 222 and 223 were the same recorded Police Station Baidam coordinates; the specific Baidam-address row 222 remains public, while row 223 is archived for audit by migration `0093_archive_duplicate_baidam_police_station`.
- **"0.00" rating badges removed.** Unrated destinations no longer display a 0-star rating.
- **788 police stations and 33 hospitals had the phone "nan"**, a leftover of the spreadsheet import, shown on district pages as "Police Station Kathmandu · nan". Migration `0085_handoff_clear_missing_marker_phones` blanks them, and a model-level guard stops future imports storing them. Only 8 of 800 active police stations have a recorded direct number, so pages point to national hotline 100 and Tourist Police 1144.
- **Superusers were labelled "Traveller".** `createsuperuser` left `role="tourist"`. It now sets `super_admin`, and migration `0086` corrects existing superusers.
- **Research lookup is read-only.** It no longer writes to the database during a public request.

## Why the two CI checks failed, and the fix

| Check | Root cause | Fix |
|---|---|---|
| **backend** (failed at 4m41s) | 1. A stale budget test expected `503` when the living-cost model is down. By design the endpoint returns `200` with the official fees and marks living costs as unavailable. 2. `main` switched `PASSWORD_HASHERS` to bcrypt (`Tourism.hashers.PrimaryBCryptSHA256PasswordHasher`), but no requirements file installs `bcrypt`. Every password hash (signup, login, `createsuperuser` and every test that creates a user) raises `ModuleNotFoundError`. | 1. The test now asserts the real contract. 2. `bcrypt==4.2.1` is pinned in `Tourism/requirements.txt`. |
| **frontend** (ran 2h17m) | `index.html` loaded Google Fonts as a render-blocking stylesheet. If the fonts CDN is slow or unreachable on the runner, the app never renders. All 114 layout checks then hit the 60 s test timeout, twice each (CI retry), and the job had no `timeout-minutes`, so it ran for hours instead of failing. | Fonts now load without blocking (`media="print"` swap plus a `<noscript>` fallback). The layout spec blocks non-loopback requests (hermetic `beforeEach`) and caps navigation at 20 s. `ci.yml` sets `timeout-minutes` (backend 30, frontend 25). |

This branch also contains the current fetched GitHub `main` tree (`336799c`, `fix(release): tolerate a release whose schema predates later model columns`), merged file by file:
bcrypt hashing, the installable public seed database (`install_public_seed_db`),
CMS inline sanitising and block audit/cache invalidation, the less flaky mail test,
and removal of the duplicate root `frontend/`, the committed `db.sqlite3`/`data.json`
and 44 committed `.pyc` files. `main` had this branch's work only up to migration
`0081`. Main retains its published migrations `0082`–`0085`; the handoff keeps its independent `0085` data cleanup under `0085_handoff_clear_missing_marker_phones`, continues through `0091_cms_cover_every_page_route`, and joins the two lines with the no-op `0092_merge_main_handoff`, then applies the data correction `0093_archive_duplicate_baidam_police_station`. The
published seed installs and migrates cleanly through `0093_archive_duplicate_baidam_police_station`.

## UI defects fixed in the final check

- **Icons drawn over typed text (site-wide).** A late `.input-field { px-4 }` rule overrode `pl-10`/`pl-11`, so 41 icon inputs in 26 files (search boxes, itinerary, login) had the icon covering the text.
- **Personal Details "Add Details" button was unstyled.** Its classes were written as bare JSX attributes.
- **Duplicate React keys on district pages.** Several stations share a name, so list items could duplicate or vanish.
- **Featured tiles.** A missing image put "Image unavailable" underneath the title. It is now a small corner tag, and 0.00 ratings are no longer shown as stars.

## Before go-live (production configuration)

| Setting | Purpose |
|---|---|
| `VITE_SITE_URL=https://<your-domain>` (Docker `--build-arg`) | Canonical, OG and sitemap URLs |
| `ROUTING_BASE_URL` | OSRM server for real road routing |
| `OPENWEATHER_API_KEY` | Weather on destination and navigation pages |
| `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | Real email (verification, password reset) |
| `GOOGLE_CLIENT_ID/SECRET`, `GITHUB_CLIENT_ID/SECRET` | Optional; the buttons appear only when set |
| `ML_SERVICE_URL` | Living-cost model and ML itinerary planner |
| `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS`, `DATABASE_URL` | Standard Django production settings |

Recommended jobs:

- `python manage.py refresh_forex` (daily; the app also self-refreshes hourly when stale).
- `python manage.py backfill_elevations --fetch` (once). About 100 high-region destinations were not fetched because Open-Meteo was overloaded during preparation.

## Known limitations

- Requirement matching uses place names and districts, since there is no official park-boundary geometry. Results are shown as "Likely applies — confirm with the official source" together with the reason.
- DEM elevations are terrain heights at the stored coordinate. Summits under-read (for example, about 8,724 m for an Everest-area point against 8,849 m surveyed). Destinations with coarse coordinates (for example, the Upper Mustang Trek record at 29.1833, 83.95) intentionally show "Elevation not recorded".
- Official fees were transcribed on 2026-09-26. Governments change fees, so re-check the linked sources periodically.
- The chatbot tries a live WebSocket (`/ws/chat/…`, defined in `asgi.py`), but the Docker image runs gunicorn (WSGI), so it falls back to plain HTTP after three attempts. Replies still work. Live streaming would need an ASGI server (daphne/uvicorn) behind the proxy.
- The ML living-cost service was not running in the development sandbox. The budget endpoint's NRB conversion and fee logic are covered by tests with a mocked ML response.
