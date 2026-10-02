# Nepal Yatra API Contract, Versioning & Deprecation Policy

**Document Identifier**: `docs/API_CONTRACT_AND_VERSIONING.md`  
**Status**: 🟢 Canonical API Standard

---

## 1. Canonical API Version

The authoritative, canonical REST API for Nepal Yatra is:

```text
/api/v1/
```

All React frontend services, mobile PWA clients, and operational tools communicate with `/api/v1/`.

### Deprecation Policy for `/api/v2/`
- Any historical `/api/v2/` endpoints that mirror `/api/v1/` are considered **experimental / legacy compatibility aliases**.
- All newly developed features, modernizations, and integrations target `/api/v1/`.
- Prior to sunsetting any `/api/v2/` route, access logs are audited over 90 days to confirm zero active client traffic.

---

## 2. Standardized Envelope & Error Formats

### 2.1 Success Responses
- Collections return paginated arrays or direct arrays:
  ```json
  {
    "count": 6701,
    "next": "/api/v1/destinations/?page=2",
    "previous": null,
    "results": [...]
  }
  ```
- Detail endpoints return resource objects directly with standard ISO 8601 timestamps:
  ```json
  {
    "id": 101,
    "name": "Pashupatinath Temple",
    "slug": "pashupatinath-temple",
    "latitude": 27.7104,
    "longitude": 85.3487,
    "created_at": "2026-01-15T08:30:00Z"
  }
  ```

### 2.2 Error Responses
Errors follow standard Django REST Framework schemas:
- **Validation Failure (`400 Bad Request`)**:
  ```json
  {
    "detail": "Invalid coordinates supplied.",
    "field_errors": {
      "latitude": ["Must be within Nepal boundaries (26.3°N - 30.5°N)."]
    }
  }
  ```
- **Unauthorized (`401 Unauthorized`)**:
  ```json
  {
    "detail": "Authentication credentials were not provided or token has expired."
  }
  ```
- **Resource Not Found (`404 Not Found`)**:
  ```json
  {
    "detail": "Destination with slug 'invalid-slug' not found."
  }
  ```
- **Service Dependency Unavailable (`503 Service Unavailable`)**:
  ```json
  {
    "status": "degraded",
    "detail": "Routing service is currently operating in fallback corridor mode."
  }
  ```

---

## 3. Core Endpoint Catalog

### 3.1 Health & Diagnostics
- `GET /health/` — Root container deployment health check (used by Render).
- `GET /api/v1/health/` — Live dependency status probe (`database`, `media`, `routing`, `weather`).
- `GET /robots.txt` — Public crawler instructions with canonical Sitemap pointer.
- `GET /sitemap.xml` — Dynamic XML sitemap indexing all public pages and approved destinations.

### 3.2 Destinations & Discovery
- `GET /api/v1/destinations/` — Paginated destination catalogue. Supports `search`, `province`, `category`, `altitude_tier`.
- `GET /api/v1/destinations/:slug/` — Comprehensive destination dossier including elevation, weather, nearby POIs, transit routes, and verified photo gallery.
- `GET /api/v1/districts/` — Canonical list of Nepal's 77 districts with provinces and headquarters.
- `GET /api/v1/nearby/?lat=&lon=&radius_km=` — Spatial proximity radar ranking destinations, hotels, and emergency facilities by geographic distance.

### 3.3 Navigation & Routing
- `GET /api/v1/navigation/route/?start_lat=&start_lon=&end_lat=&end_lon=&mode=` — Real road routing geometry and turn-by-turn maneuvers via OSRM. Returns honest fallback corridor metadata when external routing provider is unconfigured.

### 3.4 Travel Planning & Itinerary
- `GET /api/v1/travel-plans/` — Curated signature master travel plans (domestic and foreign personas).
- `POST /api/v1/itinerary/` — Dynamic multi-day itinerary generation with budget calculation and transit integration.
- `GET /api/v1/travel-plans/shared/:code/` — Immutable public travel plan viewer for shared trips.

### 3.5 Authentication & User Profile
- `POST /api/v1/auth/token/` — JWT authentication obtaining access and refresh tokens.
- `POST /api/v1/auth/token/refresh/` — JWT token renewal.
- `GET /api/v1/auth/profile/` — Authenticated traveler profile, saved favorites, and visit history.
