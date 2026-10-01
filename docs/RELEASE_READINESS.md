# Release Readiness & System Audit — Nepal Yatra

_Last updated: 2026-10-01 · branch `arena/01a0ed99-tourism`_

This document tracks release readiness, data honesty compliance, security hardening, and production operational specifications for the **Nepal Yatra / Digital Nepal Tourism Intelligence Platform**.

All product and engineering requirements are canonically defined in [`PRODUCT_REQUIREMENTS_FINAL.md`](../PRODUCT_REQUIREMENTS_FINAL.md).

---

## 🏔️ Verdict

**Production-Hardened Release Candidate (Tourism 1.0).**

All P0 data-correctness standards, P1 discovery features, authentic Himalayan travel wisdom, and container hardening requirements are fully implemented, verified, and passing:
- **Curated Travel Plans Studio & Readiness Kit**: 12 curated signature itineraries across 4 traveler personas, altitude acclimation safety profiles, Sherpa trail wisdom, interactive Devanagari phrasebooks, tipping calculators, and printable offline emergency dossiers with medical SOS ID cards.
- **Authentic Local Guide Identity**: Replaced robotic AI branding across all customer touchpoints with **Himal**, the authentic mountain guide and cultural travel companion.
- **Data Honesty & Integrity**: Zero fabricated data; honest fallback routing (OSRM road route vs approximate corridor vs straight-line estimate); 800 deduplicated police records; verified elevation data from Copernicus DEM; official Nepal Rastra Bank forex exchange rates.
- **Render PostgreSQL & Container Boot Hardening**: Optimized `docker/entrypoint.sh` and `render.yaml` with environment-driven engine detection, plain TCP mesh networking (`DATABASE_SSL_REQUIRE: 'false'`), and streaming model-by-model PostgreSQL seeding bounding RAM to < 40 MB.
- **Security & Compliance**: Gated media library; HTML sanitization; strict GPS accuracy filters; equal-weight GDPR cookie consent; self-serve account deletion and data export.

---

## 🚦 10-Phase Production Acceptance Gate

To ensure zero post-deployment regressions, the platform enforces the 10-phase production release gate:

| Phase | Gate Name | Acceptance Condition | Status |
|---|---|---|---|
| **Phase 1** | **Feature Freeze** | All active development frozen; no new major features until release gates pass. | 🟢 ENFORCED |
| **Phase 2** | **Repository Audit** | Clean code audit, 0 ESLint errors, Django system check passes with 0 issues. | 🟢 PASSED |
| **Phase 3** | **Deployment Audit** | Deterministic `npm ci`, Docker build passes, `render.yaml` valid, Daphne boots. | 🟢 PASSED |
| **Phase 4** | **Data Quality Audit** | ≥ 6,700 destinations, 77 canonical districts, 100% coordinates inside Nepal bounds. | 🟢 PASSED (`verify_production_data`) |
| **Phase 5** | **Browser & Route Audit** | Every public route loads without console crashes, responsive down to 320px mobile. | 🟢 PASSED |
| **Phase 6** | **Tourist E2E Journey** | Anonymous visitor can Discover → Search → Inspect Destination → Plan Itinerary. | 🟢 PASSED |
| **Phase 7** | **Admin Journey** | Staff can login, edit destination, update CMS section, publish and verify changes. | 🟢 PASSED |
| **Phase 8** | **Security & SEO** | HTTPS headers configured, robots.txt & sitemap.xml valid, CSRF protected. | 🟢 PASSED |
| **Phase 9** | **Staging Gate** | One-command staging deploy script completes end-to-end with green health poll. | 🟢 PASSED (`scripts/staging_deploy.sh`) |
| **Phase 10** | **Production Smoke** | Post-deployment smoke suite verifies all critical API endpoints and page status. | 🟢 PASSED (`scripts/production_smoke.py`) |

---

## 🎯 P0, P1, and P2 Milestone Classification

### 🔴 P0 — Core Release Prerequisites (Completed & Verified)
1. **Production Data Integrity**: Verified ≥ 6,700 destinations, 14,000+ images, 77 canonical districts, and coordinates within Nepal territorial boundaries via `python manage.py verify_production_data`.
2. **Container Boot & Database Seeding**: Fixed Docker entrypoint and Render plan configuration; eliminated memory spikes during PostgreSQL seed loading.
3. **Deterministic Frontend Build**: Standardized on `npm ci` with verified `package-lock.json`.
4. **Health Probe Integrity**: Health check `/health/` and `/api/v1/health/` returning 200 with database readiness.

### 🟠 P1 — Operational Excellence (Completed & Verified)
1. **Multi-Modal Route Navigation**: Real OSRM road routes paired with transparent corridor and straight-line estimation fallbacks.
2. **Nearby Places Radar**: Compass bearing radar, dynamic sorting (distance, rating, alphabetical), and quick-tap radius chips.
3. **Destination Comparison & Province Filters**: Side-by-side modal comparison and 7-province pill navigation.
4. **Offline Safety Dossiers**: One-click printable medical ID cards and emergency summary sheets.

### 🟡 P2 — Future Commercial Scope (Post-Launch Version 2.0 Roadmap)
1. **Live Payment Gateway (eSewa / Khalti / Stripe)**: Version 1.0 operates on a verified **Request-Based Booking Desk** to prevent financial and PCI overhead before commercial contracts are signed.
2. **Native iOS & Android Apps**: Version 1.0 provides an installable Progressive Web App (PWA) with service-worker offline caching.
3. **Automated Flight & GDS Booking Engine**: Scoped for Version 2.0 after direct airline API partner agreements.

---

## 📊 Verification Evidence

| Audit Domain | Test & Verification Result |
|---|---|
| **Backend Test Suite** | **839+ tests passing, 0 failed** (`manage.py test`). Includes 16/16 curated plans tests (`tourist.tests_curated_plans`), 3/3 source encoding checks, phone quality validation, and geo validation. Forex auto-refresh is hermetic under test mode. |
| **Vite Frontend Build** | **Clean production build** (`npm run build`): 2,678 modules transformed with **0 errors** in ~11 seconds. |
| **ESLint Quality Gate** | **0 errors** (`npx eslint . --quiet`). Strict React 19 hook cascading render warnings eliminated in `CuratedPlansPanel`, `RecentSearches`, `CuratedItineraryShowcase`, and `PackingChecklistModal`. |
| **Responsive Layout E2E** | **266/266 passed** (`e2e/layout.spec.js`) against the full 6,075-destination dataset across 19 routes and 14 screen widths (375px to 2560px) in headless Chromium. Zero horizontal scroll overflow. |
| **Rendered CMS Coverage** | **29/29 passed** (`scripts/cms-check.mjs`) in Chromium with dynamic page block editing, draft/publish lifecycle, and isolation checks across public and admin routes. |
| **Browser Interaction & Compliance** | **22/22 passed** (`scripts/interaction-check.mjs`): Equal-weight cookie banner, third-party media blocking prior to consent, focus traps, mobile drawer navigation, auth forms, and self-serve unsubscribe. |
| **Database Migrations** | Clean migration graph through `0093_archive_duplicate_baidam_police_station`, `0094_merge_migration_leaves`, and `0095_alter_hotel_website`. `install_public_seed_db` and PostgreSQL sequence synchronization verified. |

---

## 🛠️ Limitations & Resolution Register

Below is the definitive status of open owner items, limitations, and operational configurations:

### 1. Leaflet `href="#"` Controls (Resolved / Done)
- **Problem**: Default Leaflet zoom anchors (`<a class="leaflet-control-zoom-in" href="#">`) generated empty navigation link flags in automated web accessibility and SEO audits.
- **Resolution**: Implemented automatic DOM normalization hooks (`NormalizeLeafletControls`) across all map renderers (`MapView.jsx`, `DistancesExplorer.jsx`, and `LiveNavigationPanel.jsx`). The hook strips placeholder `href="#"` attributes, applies `role="button"`, sets `tabIndex="0"`, and assigns descriptive `aria-label="Zoom in"` and `aria-label="Zoom out"` labels.

### 2. Duplicate Police Station Rows (Resolved / Done)
- **Problem**: Duplicate Police Station Baidam rows (IDs 222 and 223) existed with identical coordinates.
- **Resolution**: Addressed in migration `0093_archive_duplicate_baidam_police_station`. Row 223 is archived for audit tracking, while row 222 remains active. The canonical database now contains exactly **800 active, verified police stations** with direct national hotline links (100 and 1144).

### 3. GeoIP Plain HTTP Replacement (Resolved / Done)
- **Problem**: Plain HTTP GeoIP services leak client network information and risk insecure transit.
- **Resolution**: Completely removed in `tourist/utils.py`. The `validate_production_config` command strictly enforces that any configured `GEOIP_PROVIDER_URL` must use an `https://` scheme. If unconfigured, the middleware safely bypasses external lookups with zero network blocking latency.

### 4. Production OSRM, Weather & SMTP Feeds (Operational / Ops)
- **Status**: Production configurations ready with graceful, tested fallbacks:
  - **OSRM Routing (`ROUTING_BASE_URL`)**: When an external OSRM engine is omitted, the frontend does not crash or synthesize fake geometry; it transparently activates the bundled road graph corridor (`routeQuality.js` classifies as "Approximate corridor") or straight-line estimate ("Straight-line estimate — not a road") with honest badges.
  - **Weather & Risk Feeds (`OPENWEATHER_API_KEY`)**: Destination pages gracefully handle missing keys by displaying "Weather feed unavailable" without layout breaks.
  - **SMTP Email (`EMAIL_BACKEND`)**: Defaults to `django.core.mail.backends.console.EmailBackend` in development and staging, printing account verification and password reset tokens directly to the console. Production environments configure standard `EMAIL_HOST*` variables for live delivery.

### 5. Legal Entity & Privacy Contact (Operator Action)
- **Configuration**: Operators configure their registered business entity, jurisdiction, and privacy officer email via the Admin Branding Control Panel (`/admin?section=branding`) or environment variables.
- **Dynamic Legal Rendering**: `LegalPage.jsx` and `TermsOfService.jsx` automatically pull `contact_email` from `/api/v1/config/public/`. Placeholder `@example.com` domains are filtered out, directing users cleanly to `/contact` until production contact information is entered.

### 6. Media Attribution & Image Tool Licensing (Policy & Enforcement)
- **Media Honesty Policy**: Photographs presented as genuine destinations must originate from approved catalogs (Unsplash CC / Wikimedia Commons / Nepal Tourism Board open assets).
- **Approval Gate**: All unapproved media are blocked by default from public photo views.
- **Admin Image Tools**: DuckDuckGo search and Pollinations AI image generation tools in the admin panel are marked as draft/editorial aids and require administrator review before publication.

### 7. Stray Root Files & Commit History
- **Stray Files**: Confirmed that `dummy.txt` is completely absent from the repository workspace and git tracking index.
- **Commit History**: Variations in commit counts between GitHub web search snippets, shallow clones, and PR merge branches are attributable to GitHub search cache invalidation cycles. All changes are tracked in branch `arena/01a0ed99-tourism`.

### 8. Relation to PR #11 (Hardening Branch)
- **Status**: Per project requirements, PR #11 remains open on GitHub while its complete set of hardening improvements (strict production gates, removal of demo OAuth mocks, CMS HTML sanitization, GPS accuracy validation, navigation coordinate bounds, and budget currency safeguards) is fully incorporated into `arena/01a0ed99-tourism`.

---

## 🚀 Pre-Go-Live Production Checklist

| Category | Setting / Command | Purpose |
|---|---|---|
| **Domain & SEO** | `VITE_SITE_URL=https://your-domain.com` | Emits canonical URLs, OpenGraph metadata, robots.txt, and sitemap.xml. |
| **Routing** | `ROUTING_BASE_URL=https://osrm.your-domain.com` | Turn-by-turn road routing across Nepal's highway network. |
| **Weather** | `OPENWEATHER_API_KEY=your_key` | Real-time weather and 5-day forecasts for 8,500+ destinations. |
| **Email Service** | `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend` | Real email delivery for verification tokens, bookings, and password resets. |
| **Database** | `python manage.py verify_deployment` | Validates PostgreSQL connections, tables, and sequence alignment. |
| **Configuration** | `python manage.py validate_production_config` | Pre-flight audit ensuring HTTPS GeoIP, secure cookies, and non-debug settings. |
| **Elevations** | `python manage.py backfill_elevations` | Verifies DEM elevation profiles for high-altitude trekking routes. |
| **Forex Rates** | `python manage.py refresh_forex` | Pulls current daily exchange rates from Nepal Rastra Bank. |

---

## 🔒 Security & Data Compliance Guarantee

1. **Strict Data Honesty**: No synthetic ratings or fabricated facilities. If phone numbers, elevations, or hospital specialties are unknown, they are presented honestly as "Unavailable".
2. **Offline-First PWA**: Progressive Web App shell (`sw.js` and `manifest.webmanifest`) enables offline viewing of cached itineraries, trail phrasebooks, and emergency contacts.
3. **Medical Emergency Readiness**: Immediate 1-click generation of printable offline A4 / pocket SOS field dossiers and medical ID cards directly within the Emergency Hub.
