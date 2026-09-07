# Recommendation Pipeline (Phase 2 documentation)

Honest map of every surface that produces recommendations, and what it calls.
Goal: one canonical ML-backed recommendation path; everything else either
delegates to it or is clearly a different *kind* of result (search vs recs).

## Canonical path
```
React (Recommendation.jsx / Dashboard)
  -> GET /api/v1/recommendations/personalized        (Django views_compat.RecommendationsPersonalizedView)
  -> Django (interests + optional GPS)
  -> ML service  POST /recommendation                (ml_service/api/recommendation.py)
  -> TF-IDF / RandomForest model over processed_data
  -> returns ranked destinations (ml_score, cover, budget, season)
```

## Other recommendation-producing surfaces
| Surface | Calls | Kind | Consistent with canonical? |
|---|---|---|---|
| `/recommendation` page | `recommendationApi.getRecommendations` → `/recommendations/personalized` | ML recs | ✅ same canonical view |
| Dashboard "for you" | `recommendationApi.getPersonalized` | ML recs | ✅ same canonical view |
| Home featured grid | `adminApi.getPublicFeaturedDestinations` + `destinations?featured=true` | curated/admin | ➖ deliberate (editorial, not ML) |
| Chatbot | `chatbot/services.find_matching_destinations` (DB text match) + `match_published_packages` | search/packages | ➖ deliberate: it answers a *query*, not a profile |
| Similar destinations (detail) | destinations related-by category/district | content-based | ➖ deliberate, cheap, no fake scores |

## Cold-start & failure behaviour (verified)
- No interests/GPS → canonical view falls back to top-rated public destinations
  with `source: "fallback_top_rated"` (labelled, not fake-personalized).
- ML service down → Django returns the labelled DB fallback rather than an error
  or silent fake; the UI shows recorded destinations.

## Guardrails agreed
- Never invent a score: every ML item carries `ml_score`; fallbacks carry a
  `source` label so the frontend can say "popular near you" vs "picked for you".
- Chatbot must not claim personalization; it presents matched destinations and
  published packages grounded in DB records.
