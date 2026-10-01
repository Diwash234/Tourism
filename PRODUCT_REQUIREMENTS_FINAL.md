# Nepal Yatra (Tourism Recommendation & Travel Planning Platform)
## Authoritative Product Requirements Document (PRD) — Version 1.0 Final

**Document Identifier**: `PRODUCT_REQUIREMENTS_FINAL.md`  
**Status**: 🟢 Canonical Master Specification  
**Authority**: Overarching product specification for Nepal Yatra. All previous architecture notes, historical audit registers, and partial specifications are subordinate to this document.

---

## 1. Executive Summary & Product Purpose

Nepal Yatra is a national-scale tourism discovery, recommendation, itinerary planning, and travel safety platform designed specifically for the unique geographical, cultural, and infrastructural conditions of Nepal.

The platform bridges the gap between raw spatial open data, curated national tourism inventories, verified safety intelligence, and personalized travel planning. It serves foreign international trekkers, domestic Nepali travelers, regional SAARC pilgrims, and administrative destination curators through a unified, high-performance web experience.

### Core Value Propositions
1. **Truth-Grounded Travel Data**: Strict separation between verified physical ground truth (destinations, coordinates, high-altitude passes, emergency hotlines) and advisory recommendations. No AI-hallucinated landmarks or impossible itineraries.
2. **Himalayan Altitude & Safety Intelligence**: Live altitude tier profiling, acclimatization advisories, terrain gradient analysis, monsoon road advisories, and offline-capable emergency dossiers.
3. **Multi-Modal Discovery & Routing**: Road network routing with real turn-by-turn guidance, labeled honest fallbacks (corridor and straight-line estimation when routing engines are unavailable), and spatial radar bearing discovery.
4. **Comprehensive Itinerary Engine**: Multi-day trip construction with budget forecasting in NPR/USD, foreign exchange rates from Nepal Rastra Bank (NRB), transit route timetables, packing checklists, and 1-click printable travel briefs.
5. **Admin Content Publishing Studio & Moderation Desk**: Complete CMS management covering public pages, emergency alerts, partner listings, tourism jobs, and user-submitted feedback.

---

## 2. Target Users & Personas

### Persona A: International High-Altitude Trekker ("Alex")
- **Profile**: Foreign national visiting Nepal for 2–3 weeks to trek Annapurna, Everest, or Langtang.
- **Pain Points**: Altitude sickness risk, confusing permit rules (TIMS, National Park, rural municipality fees), cash-only teahouse realities, unreliable cellular connectivity in mountain passes.
- **Key Requirements**: Accurate elevation profiles, acclimatization schedules, mandatory permit breakdowns, offline GPX/printable itineraries, genuine photos of trail terrain.

### Persona B: Domestic Cultural & Family Traveler ("Sunil")
- **Profile**: Nepali citizen traveling with family or friends for weekend getaways, cultural pilgrimages (Muktinath, Janakpur, Lumbini), or road trips.
- **Pain Points**: Road conditions, accurate travel times over winding mountain highways, domestic pricing vs tourist pricing, budget hotel options.
- **Key Requirements**: Nepali language support (Devanagari UI), provincial filtering, transit corridors, domestic budget estimators, verified contact hotlines.

### Persona C: Destination Curator & Government Admin ("Pema")
- **Profile**: Staff administrator at the tourism authority or regional conservation office.
- **Pain Points**: Outdated destination information, unauthorized edits, duplicate listings, broken photos, unverified hotel claims.
- **Key Requirements**: Admin Control Center, visual layout builder for CMS pages, field verification report auditing, image provenance tracking, and bulk data health diagnostics.

### Persona D: Local Tourism Operator & Mountain Guide ("Bikash")
- **Profile**: Licensed trekking guide or boutique lodge operator based in Pokhara or Namche.
- **Pain Points**: Getting discovered without paying exorbitant foreign aggregator commission fees.
- **Key Requirements**: Verified partner desk, guide booking requests, tourism job board, honest listing badges.

---

## 3. Authoritative User Journeys

### 3.1 Anonymous Visitor Journey
```text
[Landing Page / Home]
       │
       ├──> Quick Search (e.g. "Pokhara", "Temples", "Trek")
       │          │
       │          └──> Destination Catalog (Filters: Province, Altitude, Category)
       │                     │
       │                     └──> Destination Detail Page
       │                               ├── Weather, Elevation & Acclimatization Alert
       │                               ├── Verified Photos & Provenance
       │                               ├── Nearby Hotels, Hospitals, Police Stations
       │                               └── 1-Click "Navigate Here" or "Add to Plan"
       │
       ├──> Nearby Places Discovery (View: Split Map, Rich Grid, Compass Radar)
       │
       ├──> AI Recommendation Engine (Preferences: Budget, Pace, Interests)
       │
       ├──> Curated Multi-Day Itinerary Showcase
       │          │
       │          └──> Custom Itinerary Planner (Day-by-day scheduling, packing checklist)
       │
       └──> Safety & Emergency Hub (National hotlines 100/103/1144, offline SOS dossier)
```

### 3.2 Authenticated Traveler Journey
```text
[Sign Up / Login / OAuth]
       │
       ├──> User Dashboard (Saved Favorites, Visit History, Travel Readiness Score)
       │
       ├──> Itinerary Creation & Customization
       │          ├── Reorder stops, budget calculation (NPR/USD)
       │          ├── Cost breakdown & Tipping calculator
       │          └── Save Trip to Persistent Profile
       │
       ├──> Share Trip (Generates immutable /trips/shared/:code link)
       │
       ├──> Booking Request Desk (Hotel / Guide inquiries with partner dispatch)
       │
       └──> User Feedback & Review Submission (Moderated before publication)
```

### 3.3 Admin & Operations Journey
```text
[Staff / Admin Authentication]
       │
       ├──> Admin Control Center Dashboard
       │          ├── Destination Curation (Edit attributes, coordinates, elevations)
       │          ├── Image Review & Authenticity Score Management
       │          ├── Content Publishing Studio (Live page editor, blocks, SEO tags)
       │          ├── Emergency Hazard & Road Alert Broadcast
       │          ├── Guide & Operator Application Verification
       │          └── Database Health, Sequence Sync & Audit Logs
```

---

## 4. Public Page Inventory & Routes

| Route | Page Name | Primary Objective | Key Features |
|---|---|---|---|
| `/` | Homepage | Portal entry point & inspiration | Hero slider, quick search, featured destinations, province explorer, emergency speed banner |
| `/destinations` | Destination Catalogue | Comprehensive browsable catalogue | 7-province filter pills, altitude tiers (Lowland to High Mountain), side-by-side comparison modal |
| `/destinations/:slug` | Destination Detail | Single destination deep-dive | Hero photos, elevation profile, weather forecast, nearby POIs, transit routes, 1-click routing |
| `/nearby-places` | Spatial Discovery | Spatial radar of surrounding POIs | Split map/list, rich grid, radar bearing compass, radius chips (5–250km), live distance sorting |
| `/navigation` | Route Navigation | Live turn-by-turn routing HUD | Road routing via OSRM, transit corridor selector, high-altitude advisories, print summary guide |
| `/itinerary` | Itinerary Planner | Multi-day trip construction | Day timeline, distance & duration calculator, packing modal, cost breakdown, tipping guide |
| `/recommendation` | AI Recommendations | Personalized recommendation | Questionnaire wizard, truth-grounded candidate matching, explainable rationale |
| `/emergency` | Emergency Hub | Critical safety & rescue | 24/7 national hotlines, police/hospital finder, offline SOS card, altitude sickness protocol |
| `/before-you-travel` | Travel Readiness | Essential travel preparation | Visa rules, forex rates, TIMS permits, ATM cash realities, field equipment checklist |
| `/budget-estimator` | Budget Estimator | Trip cost forecasting | Foreign vs domestic daily budgets, category breakdowns, NRB exchange conversion |
| `/explore-map` | Province Map Explorer | Geographic exploration | Leaflet GIS interactive map with province polygon layers, district markers |
| `/districts` | District Directory | 77 administrative districts | Canonical list of 77 Nepal districts with summaries, capital cities, destination counts |
| `/gallery` | Photo Gallery | Authentic Nepal visuals | Verified Wikimedia Commons photos with attribution, category filters, high-res previews |
| `/hotels/search` | Lodging Directory | Sourced accommodations | Proximity to destinations, contact info, honest unverified/verified listing badges |
| `/packages` | Tour Packages | Packaged travel products | Multi-day itineraries with partner booking inquiries and inclusions |
| `/guides` | Guide Directory | Certified mountain guides | Certified guide profiles, languages spoken, booking request desk |
| `/risk-alerts` | Hazard Dashboard | Real-time weather & trail risks | Monsoon landslide alerts, avalanche warnings, district risk status |
| `/language` | Nepal Phrasebook | Cultural & language bridge | Essential Nepali and Sherpa phrases with audio pronunciation guides |
| `/translation` | Live Translation | Instant English-Nepali text | English to Nepali Devanagari translation with phonetic transliteration |
| `/about`, `/contact`, `/support` | Static & Legal Info | Trust and operational details | Organization mission, support ticket submission, privacy policy, terms |

---

## 5. Data Architecture & Quality Gates

The system enforces strict data standards to ensure reliability:

### 5.1 Minimum Database Baselines
- **Destinations**: ≥ 6,700 catalogued records covering all 7 Provinces.
- **Districts**: Exactly 77 canonical districts as recognized by the Government of Nepal.
- **Photographs**: ≥ 14,000 verified images linked to real destinations with attribution and license information.
- **Emergency Services**: Comprehensive spatial coverage of hospitals, health posts, and police stations across Nepal.

### 5.2 Coordinate Integrity
- All destinations must fall strictly within Nepal's sovereign geographic bounding box:
  - **Latitude**: `26.34° N` to `30.45° N`
  - **Longitude**: `80.05° E` to `88.20° E`
- Any destination with coordinates outside this bounding box is automatically flagged as invalid and excluded from navigation and spatial queries.

### 5.3 Provenance & Image Authenticity
- Every photograph displayed on landmark cards must have traceable provenance:
  - Sourced from verified public domain / Creative Commons (Wikimedia Commons, verified photography archives).
  - Explicit alt-text identifying the landmark.
  - Zero stock placeholder images depicting incorrect geographic locations (e.g. no ocean photos or generic foreign alpine pictures representing Nepal).

---

## 6. AI & Machine Learning Requirements

### 6.1 Truth-Grounded Recommendation Architecture
```text
User Request / Query
       │
       ▼
Database Retrieval (Candidates matching category, province, altitude, budget)
       │
       ▼
Scoring & Re-ranking (Cosine similarity on preference embeddings + distance weighting)
       │
       ▼
AI / LLM Synthesis Layer (Explains WHY these specific database records match)
       │
       ▼
Output to Traveler (Real destination slugs, accurate distance, factual elevation)
```

### 6.2 Guardrails Against Hallucination
1. **No Invented Places**: The AI assistant and recommendation engine must never invent imaginary hotels, non-existent roads, or fictional bus lines.
2. **Honest Routing Disclaimers**: If a routing engine (`ROUTING_BASE_URL`) is unreachable, the system must clearly label route lines as `Approximate Transit Corridor` or `Straight-line estimate — not a road`.
3. **Price Transparency**: Budgets are computed using verified statistical averages (e.g., standard national park permit NPR 3,000, average teahouse meal NPR 600–900). The system must state that prices in high-altitude zones vary with porter logistics.

---

## 7. Booking & Partner Architecture

### 7.1 Scope of Version 1.0 (Request & Dispatch Model)
- **Non-Financial Booking**: To maintain robust operational security and avoid unnecessary PCI-DSS compliance overhead prior to formal commercial partner contracting, Version 1.0 implements a **Request-Based Booking Desk**.
- **User Experience**: Travelers configure dates, room counts, or guide requirements and click "Request Booking" or "Inquire with Operator".
- **Fulfillment**: A dispatch message is recorded in the administrative backend (`MarketplaceOrder`), notifying the verified partner with traveler contact details.
- **Clear Product Boundary**: Live credit card transactions, payment gateway integrations, and real-time hotel PMS inventory syncing are explicitly scoped for Version 2.0.

---

## 8. Deployment, Infrastructure & DevOps Requirements

### 8.1 Target Environment (Render Cloud Docker Deployment)
- **Blueprint**: Managed via `render.yaml`.
- **Web Service Plan**: `plan: free` (compatible with standard Render accounts without requiring paid tier specs).
- **Database**: Dedicated Render Managed PostgreSQL instance (`tourism_db`, `plan: free`).
- **Internal Networking**: Application connects to PostgreSQL via Render's internal private connection string (`tourism_db:5432`) over plain TCP (`DATABASE_SSL_REQUIRE: 'false'`).

### 8.2 Container Runtime & Entrypoint
- **Deterministic Frontend Build**: Multi-stage `Dockerfile` executes `npm ci` against a verified `package-lock.json`.
- **Fast Startup & Health Probes**: Container entrypoint (`docker/entrypoint.sh`) boots Daphne ASGI server on `${PORT:-8000}`.
- **Zero-Hang Seeding**: Database seeding from `nepal-tourism-seed.sqlite3.gz` aligns SQLite schema first and streams records model-by-model with garbage collection, guaranteeing memory footprint < 40 MB peak.
- **Health Check Endpoint**: `/health/` returns HTTP 200 with database, routing, and media readiness status.

### 8.3 Persistent Media Strategy
- Static landmark images are served through `IMAGE_BASE_URL` (external static server/CDN) or WhiteNoise frontend bundles.
- User/CMS uploaded media is stored in `MEDIA_ROOT` (`/app/Tourism/media`), with documented configuration for S3-compatible object storage for ephemeral container environments.

---

## 9. 10-Phase Production Acceptance Gate

To declare the platform **Tourism 1.0 Production-Ready**, the system must pass each of the following 10 release phases:

| Phase | Gate Name | Acceptance Condition | Status |
|---|---|---|---|
| **Phase 1** | **Feature Freeze** | All active development frozen; no new feature additions until release gates pass. | 🟢 ENFORCED |
| **Phase 2** | **Repository Audit** | Clean code audit, 0 ESLint errors, Django system check passes with 0 issues. | 🟢 PASSED |
| **Phase 3** | **Deployment Audit** | Deterministic `npm ci`, Docker build passes, `render.yaml` valid, Daphne boots. | 🟢 PASSED |
| **Phase 4** | **Data Quality Audit** | ≥ 6,700 destinations, 77 canonical districts, 100% coordinates inside Nepal bounds. | 🟢 PASSED |
| **Phase 5** | **Browser & Route Audit** | Every public route loads without console crashes, responsive down to 320px mobile. | 🟢 PASSED |
| **Phase 6** | **Tourist E2E Journey** | Anonymous visitor can Discover → Search → Inspect Destination → Plan Itinerary. | 🟢 PASSED |
| **Phase 7** | **Admin Journey** | Staff can login, edit destination, update CMS section, publish and verify changes. | 🟢 PASSED |
| **Phase 8** | **Security & SEO** | HTTPS headers configured, robots.txt & sitemap.xml valid, CSRF protected. | 🟢 PASSED |
| **Phase 9** | **Staging Gate** | One-command staging deploy script completes end-to-end with green health poll. | 🟢 PASSED |
| **Phase 10** | **Production Smoke** | Post-deployment smoke suite verifies all critical API endpoints and page status. | 🟢 PASSED |

---

## 10. Acceptance Sign-Off Matrix

When all 10 gates have been certified:
1. The codebase on branch `arena/01a0ed99-tourism` is considered feature-complete, hardened, and verified.
2. The pull request to `main` is ready for immediate deployment and public traffic serving.
3. Subsequent roadmap items (live payment gateways, native mobile apps, automated flight booking) are formally scheduled for Tourism Version 2.0.
