# Master Upgrade Audit — Integrated Nepal Tourism Platform

Audit date: 2026-08-18

This document maps the existing implementation to the master requirements. The project remains one React + Django + SQLite application; no second recommendation engine, risk API, admin dashboard, or database is introduced.

| Existing feature | Required update | Existing/affected implementation | Status |
|---|---|---|---|
| Database-backed destination catalog | Keep SQLite as live source; CSV only import/export/ML exchange | `tourist.models.Destination`, destination ViewSet, CSV management commands | Implemented |
| Existing mood/content recommender | Preserve base score; add preferences, feedback, popularity, safety, services and routes | `MoodRecommendationsView`, `Recommendation.jsx` | Implemented; diversity/current-warning reranking tracked below |
| Destination images and gallery | Destination-ID relationship, verified media only, no unrelated fallback | `DestinationImage`, serializers, `imageUtils.js`, cards/details/gallery | Implemented |
| Structured destination features | Difficulty, duration, budget and 0–5 experience scores | `DestinationFeatureProfile` | Implemented |
| Risk/news separation | Verified news remains distinct and cannot become warning automatically | `RiskNewsReport`, `/news`, risk response | Implemented |
| User place submission | Expand to hotels, hospitals, police, bank/ATM, blood bank, fire, ambulance, pharmacy, route and media | `InfrastructureSubmission`, `InfrastructureMedia`, `/submit-service` | Implemented |
| Moderation | Pending → approved/rejected/needs correction; admin identity/time; DB + CSV publication | `InfrastructureModerationView`, `community_data_service.py`, admin panel | Implemented |
| CSV compatibility | Preserve existing schemas; write richer additions to compatible community CSVs; merge verified risk rows | `community_data_service.py`, `community_*.csv`, existing destination/risk CSVs | Implemented |
| Emergency page | Nepal-wide coordinate search and multiple distance-ranked facilities | `emergency_service.py`, destination emergency API, `Emergency.jsx` | Implemented |
| Facility provenance | Source, URL, verified/verified_at/updated_at/opening/emergency availability/media | Hospital, PoliceStation, Hotel, OSMEssentialService | Implemented |
| Incorrect nearby counts/distances | Haversine filtering, configurable radius, nearest-outside-radius disclosure | OSM nearby view and emergency service | Implemented |
| National versus local numbers | Never invent local number; explicit national fallback | emergency API/UI | Implemented |
| Nepal-wide risk | Destination-specific endpoint, exact or disclosed nearest baseline | `risk_service.py`, destination risk API, risk panel | Implemented |
| Risk layers | Keep current warnings, history, traveler evidence and model indicator separate | `RiskIncident`, `CurrentHazard`, risk response/UI | Implemented |
| DHM/BIPAD/news extensibility | Provider-neutral ingestion plus scheduled HTTPS connectors | `risk_ingestion.py`, `official_connectors.py`, `sync_official_risk` | Implemented; URLs remain deliberately unconfigured until authorities approve machine endpoints |
| Geofenced alerts | Notify users in 2–4 km radius and opted-in accepted family links | Alert signal and admin advisory form | Implemented |
| Itinerary integration | Add nearest approved hotels, hospitals, police and essentials per day | itinerary API enrichment and `Itinerary.jsx` | Implemented |
| Feedback/correction | Admin queue, correction categories and evidence media | `UserFeedback`, `FeedbackEvidence`, Contact page, admin feedback APIs | Implemented |
| Admin ML pipeline | Export approved rows; one-click training; version/status history | `MLDataPipelineView`, `MLTrainingRun`, admin panel/status API | Implemented |
| Recommendation diversity | Avoid category/district near-duplicates while preserving base model | `MoodRecommendationsView` | Implemented (MMR-style category/district reranking) |
| Current official warning penalty | Stronger than historical risk; mark critical destination unavailable | recommender + `CurrentHazard` | Implemented |
| Recommendation events | Search/view/save/select event history and explicit consent | `RecommendationEvent`, consent-gated API and Recommendation UI | Implemented |
| Observation station values | Station, unit, trend, observed time, destination distance | `RiskObservation`, ingestion adapter and risk response | Implemented |
| Road distance | Distinguish straight-line from routed road distance | navigation/route engine, optional OSRM-compatible routing connector, `/routing/metrics/` | Implemented with explicit unconfigured/unavailable fallback; actual routes require configured graph service |
| Acceptance matrix | Pokhara, Kathmandu, Rara, Mustang, Jumla, Humla, Chitwan, Lumbini, Dhangadhi, Dadeldhura | `acceptance_check_nepal` command + tests | Implemented; current data gaps are reported rather than fabricated |

## Data-quality rules

1. Missing data remains unavailable/unverified; it is never fabricated.
2. A model indicator is never labeled an official warning.
3. External image captions do not prove that a photo depicts a destination.
4. User records are excluded from trusted CSV/ML data until admin approval.
5. Straight-line distance and estimated travel time are labeled; neither is falsely called road distance.
6. Source and freshness metadata travel with safety-critical records.

## Latest production data audit

The operational audit intentionally reports gaps rather than upgrading imported rows to verified:

- 8,524 approved destinations
- 218 missing coordinates
- 8,523 missing municipality
- 925 missing district
- 6,639 missing verified destination media
- 393 imported hospitals, 0 independently admin/authority verified
- 641 imported police stations, 0 independently admin/authority verified
- 1,552 imported hotels, 0 independently admin/authority verified
- 0 persisted essential-service rows

Use `python manage.py audit_data_quality --output reports/data-gaps.csv` to reproduce and prioritize this work. These are data-acquisition tasks; populating them without authority records would violate the no-fabrication requirement.
