# Master Implementation Prompt — Compliance Matrix (verified against code)

Audited at branch `arena/01a07999-tourism`. Every ✅ cites the file/test that
proves it. Sections are grouped; the master prompt's numbering is kept.

## Already satisfied (evidence in-repo)

| § | Requirement | Evidence |
|---|---|---|
| 2, 16, 64 | Tourism intelligence separate from road routing; provider abstraction | `navigation/routing_provider.py`, `osrm_provider.py`, `fallback_providers.py`; tourism graph untouched for AI (`tourist/routing_service.py`) |
| 4, 5 | Provider layer, no scattered vendor calls | navigation app + `tourist/location/search_service.py`; providers env-configured |
| 6, 47 | Provenance/verification/audit | `Destination.source/provenance/field_sources`, `DestinationImage.verification_status`, `DestinationAuditLog`, revision restore, `import_conflicts` |
| 7, 10, 74 | Place model + 77-district coverage, no fake coverage | 6,691 real destinations, 77/77 districts (8 gap-fill places in Rautahat/Rolpa are real, named, sourced); `normalize_district_names` command |
| 8, 9 | AI research jobs / candidates never auto-verified | `DiscoveryJob`, `TourismJob`, `candidate_matches`, proposals → admin approval (403-tested) |
| 12 | Education/heritage discovery | taxonomy + `categorize_existing` keyword rules (museums/heritage/culture); 0 null categories |
| 13, 43 | Hotels dynamic, no hard-coded fallback | `Hotel` model + radius/district search; audit found zero hard-coded hotel lists |
| 14, 44 | Emergency discovery | `Hospital`, `PoliceStation` + `places/nearby/`, `along-route/` |
| 15, 75 | straight-line vs road distance; no fake navigation | fallback sources labelled `graphml_fallback`/`straight_line_fallback`; `navigation_grade` gates live navigation; notes on every estimate |
| 17, 18 | Legacy `/navigation/route` contract on real road routing; real geometry drawn | `views_compat.NavigationRouteView` now uses the provider chain first (tests: `LegacyRouteContractTests`); `LiveNavigationPanel` draws provider geometry |
| 19, 20 | Transport profiles; flight separate | `PROFILE_BY_MODE` (only hosted profiles exposed); flight never road-routed (tested) |
| 21–28 | GPS, map matching, states, turn-by-turn, off-route, reroute, alternatives | `navigation/map_matching.py`, `navigation_service.py`, `useTurnByTurn.js` state machine, GPS replay fixtures (`navigation/fixtures/gps/*.json`) |
| 22, 58 | Privacy/consent | watchPosition only after explicit Start; sessions store snapshots, **no GPS history**; End clears watch + server session |
| 29–33 | Itinerary↔navigation, corridor services | `/navigation/itinerary-route/`, next-stop flow, `/navigation/along-route/` (route-distance sorted) |
| 34 | Central geo service | `map_matching.py` + `search_service.py` (no geo math in React) |
| 35, 36, 61 | Weather/safety as labelled context; freshness; graceful fallback | `/navigation/route-context/` ("never alter the route" note), OpenWeather best-effort labelled, provider→graph→line chain |
| 37 | Fallback order, never invent | chain order in `route_engine.provider_chain()`; last resort is an explicitly labelled straight-line estimate |
| 38, 39 | Recommendation + geographic expansion | discovery/recommendation views with district→province→nationwide expansion (prior milestones) |
| 40 | No localStorage-as-database | audited: localStorage only for auth token/theme/i18n/prefs |
| 41, 42, 45, 46, 50, 51 | Admin command center, candidate review, override priority, quality | DataExplorer + ContentLifecycle + MediaApprovals panels; `/admin/data-integrity/`, completeness indicator; admin>AI override via lifecycle |
| 48 | Guide/staff workflow | staff drafts → submit_review → admin approval (E2E-tested) |
| 52, 53 | Unified search; honest destination pages | `/places/search/`; "Not recorded" for empty fields (prior commit `dad97ac` lineage) |
| 54–56 | Navigation UI, states, voice | `LiveNavigationPanel.jsx`, `speechSynthesis` with repeat suppression |
| 60, 62 | API audit, security | capability permissions, 403 tests, rate limits (route 30/min, 429-tested), keys env-only |
| 65, 66 | Route cache, corridor search | `cached_route` (provider+coords+mode key), corridor prefilter + projection |
| 73 | Tests | backend 449 tests, E2E 66 live checks, GPS replay fixture suite, `validate_navigation_routes` (7 canonical routes) |
| 76 | No fake "live" labels | diagnostics/health endpoints; fallback banners in UI |

## Gates that require the deployment host (external, honest)

1. **Real OSRM 7/7**: `ROUTING_BASE_URL=<osrm> python manage.py validate_navigation_routes`
   then `--write-baseline` to arm regression protection. Sandbox network
   cannot reach external routing servers (verified repeatedly).
2. **Physical-device GPS run** — permissions, sensors, app lifecycle. The
   algorithmic half (jitter, wrong turn, tunnel, arrival) is covered by the
   committed replay fixtures; the device half cannot exist in CI.

## Deliberate non-goals (per prompt's own rules)

- No `Place` super-model migration: `Destination` is the canonical model;
  unifying would be churn without user value (§63 says avoid duplicated
  models — we have none duplicated).
- No offline packages / OSRM cluster / Redis-Celery yet (§57 says design for
  it, don't claim it): the provider abstraction and cache layer are the
  designed seams.
