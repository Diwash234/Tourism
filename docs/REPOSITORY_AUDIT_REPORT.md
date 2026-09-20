# AUDIT COMPLETE

**Repository:** `Diwash234/Tourism`, branch `arena/01a07999-tourism`, tip `dacf3d6`
(all numbers below re-verified from the working tree this turn; test suite re-run: 449 OK).

**Backend:** Django 5.0.6 + DRF. 13 apps (tourist, navigation, safety, admin_panel,
audit, booking, chatbot, dataset, media_app, notifications, system_health,
translation + project). 96 models in `tourist` alone; 199 URL patterns in
`tourist/urls.py` + 12 in `navigation/urls.py`. Auth: JWT (simplejwt) + OAuth
callback flows; staff capabilities enforced per-action (403-tested).
84 migrations; SQLite dev / Postgres-ready via env; 85 `config()` env vars,
zero secrets committed (frontend secret scan: 0 hits).

**Frontend:** React 18 + Vite + Tailwind, 74 page components; axios service
layer with relative URLs (dev proxy); Leaflet maps via `MapView` +
react-leaflet in `LiveNavigationPanel`; state = hooks/context (no Redux);
`eslint src/` 0 errors; production build clean.

**Database:** 6,691 public destinations (all 77 districts, 0 null categories,
0 null/out-of-bbox coordinates), hotels/hospitals/police/restaurants with real
rows, `RouteDiagnostics` + `NavigationSession` tables, audit log + revisions,
import-conflict protection. `db.sqlite3` is the committed dev dataset.

**Current Navigation:** `navigation/` app — provider abstraction
(OSRM env-configured) → labelled fallbacks (`graphml_fallback`,
`straight_line_fallback`); endpoints: road-route, progress, itinerary-route
(multi-stop), select-alternative, along-route, route-context, modes,
diagnostics, health, end, sessions/active, debug/replay. Frontend
`useTurnByTurn` state machine + watchPosition + reroute cooldown +
`navigation_grade` gating (estimates cannot enter live navigation).
GPS replay fixtures (6) run in CI. Legacy `/navigation/route` contract rides
the same provider chain.

**Current Tourism Data:** OSM-imported + curated; provenance fields
(source, provenance, field_sources, imported_data), verification states on
media + submissions, `DiscoveryJob`/`TourismJob` research infrastructure,
candidate/proposal → admin-approval workflow.

**Current AI:** advisory only (`ai_recommendation_status`); publishing is a
human admin action; Himal AI recommendations from real DB rows.

**Current External Providers:** OSRM (env, blocked in sandbox — mock-verified),
OpenWeather (env key, degrades labelled), ML microservice (`ml_service/`,
optional with internal fallback), Overpass/OSM import (historical; network
blocked here), Twilio/FCM (env, optional).

**Major Gaps:** none in code for the master prompt's acceptance list —
see `docs/MASTER_PROMPT_COMPLIANCE.md`. Remaining gaps are all external
dependencies (below) and the deliberate non-goals listed there.

**Files Requiring Modification (for remaining roadmap):** none mandatory;
future work (elevation, offline packages, provider failover) extends
`navigation/` seams without touching tested cores.

**New Components Required:** none for current scope.

**Migration Required:** NO (pending work is configuration, not schema).

**External Credentials Required:** real OSRM host (`ROUTING_BASE_URL`),
OpenWeather key (optional), OAuth app creds, production Postgres DSN +
`SECRET_KEY`, cron on the real host, a device for GPS testing, a host where
`npx playwright install --with-deps` can run.

**Implementation Phases (executed, in order):**
1. Data foundations — taxonomy, district normalization, 77-district coverage, diagnostics
2. Publication lifecycle — drafts-by-default, publish/unpublish, media approval
3. Navigation subsystem — providers, GPS, rerouting, turn-by-turn
4. Production hardening — diagnostics, health, strict source contract, validation
5. Itinerary integration — multi-stop, alternatives, context layers, next-stop
6. Testability — GPS replay fixtures, session model, route-regression baseline
7. Master-prompt audit — §17 legacy contract on road routing + compliance matrix

---

## BLOCKED / PARTIAL register (definition-of-done rule #78)

| Requirement | Status | Implemented portion | Missing dependency | Current fallback | Completion requires |
|---|---|---|---|---|---|
| Real OSRM road routing in production | PARTIAL | Full provider + 7/7 validation via local mock; env-configured | Network access to an OSRM server | Labelled `graphml_fallback` / `straight_line_fallback`; live navigation gated off for estimates | `ROUTING_BASE_URL` on host → `validate_navigation_routes` → `--write-baseline` |
| Physical-device GPS verification | BLOCKED | Algorithmic half CI-covered by 6 replay fixtures | A physical phone/browser | — | Manual run through `docs/PRODUCTION_OPERATIONS.md` checklist |
| Live weather along routes | PARTIAL | Context-layer wiring + honest "unavailable" label | `OPENWEATHER_API_KEY` | Labelled unavailability | API key in env |
| OAuth login | PARTIAL (path verified) | Callback flow proven end-to-end with mocked provider (`OAuthCallbackFlowTests`: exchange → userinfo → user link, no duplicates, JWT issued; failure path 400) | OAuth app credentials | Password auth | Provider credentials only — code path is verified |
| Production datastore | PARTIAL | Postgres-ready settings, backup command | Postgres DSN | SQLite dev DB | DSN + `SECRET_KEY` in env |
| Browser-spec E2E (Playwright) | BLOCKED (cause verified) | 66-check API-level E2E runs everywhere | Playwright CDN blocked at network level in CI sandbox (TLS socket disconnect, verified); no root for system deps | API E2E | `npx playwright install --with-deps` on host |

**Host runner:** `bash scripts/close_production_gates.sh` executes every
runnable gate in register order (OSRM 7/7 → baseline → weather → OAuth →
Postgres → browser E2E → API E2E/lint/build) and prints the manual GPS
checklist. Paste its output back into this register to close entries.
