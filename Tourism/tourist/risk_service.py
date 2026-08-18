"""Destination risk aggregation.

Historical evidence, current observations and the model indicator deliberately
remain separate.  A model score must never be presented as an official warning.
"""
from collections import Counter
from math import atan2, cos, radians, sin, sqrt

from django.db.models import Avg, Q
from django.utils import timezone

from .models import Alert, CurrentHazard, RiskIncident, TravelRiskFeedback

SEVERITY_WEIGHT = {"low": 1.0, "moderate": 2.0, "high": 3.5, "critical": 5.0}
HAZARD_LABELS = dict(RiskIncident.HazardType.choices)


def _haversine_km(lat1, lon1, lat2, lon2):
    if None in (lat1, lon1, lat2, lon2):
        return None
    lat1, lon1, lat2, lon2 = map(lambda x: radians(float(x)), (lat1, lon1, lat2, lon2))
    dlat, dlon = lat2 - lat1, lon2 - lon1
    value = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 6371 * 2 * atan2(sqrt(value), sqrt(1 - value))


def _level(score):
    if score >= 72:
        return "critical"
    if score >= 50:
        return "high"
    if score >= 26:
        return "moderate"
    return "low"


def build_destination_risk(destination):
    now = timezone.now()
    incidents = list(destination.risk_incidents.all()[:100])
    feedback_qs = TravelRiskFeedback.objects.filter(
        Q(destination=destination) | Q(destination__isnull=True, destination_name__iexact=destination.name)
    )
    feedback = list(feedback_qs[:100])

    hazard_counts = Counter(i.hazard_type for i in incidents)
    feedback_hazards = Counter(
        (f.hazard_witnessed or "").strip().lower().replace(" ", "_")
        for f in feedback if (f.hazard_witnessed or "").lower() != "none"
    )
    hazard_counts.update(feedback_hazards)

    baseline = getattr(destination, "risk_analysis", None)
    baseline_match = None
    if baseline:
        baseline_match = {"destination": destination.name, "distance_km": 0.0, "method": "exact destination"}
    else:
        # Imported CSV baselines do not cover every DB row. Reuse the nearest
        # baseline in the same district rather than returning the same zero-risk
        # answer everywhere, and disclose that spatial proxy to the frontend.
        from .models import RiskAnalysis
        district_candidates = list(RiskAnalysis.objects.select_related("destination").filter(
            destination__district__iexact=destination.district
        )[:250])
        # Some imported rows use old/transliterated district names. If there is
        # no same-district baseline, search all imported baselines spatially so
        # every coordinate-backed Nepal destination still receives a disclosed
        # proxy instead of the same zero-risk response.
        candidates = district_candidates or list(
            RiskAnalysis.objects.select_related("destination").exclude(
                destination__latitude__isnull=True
            ).exclude(destination__longitude__isnull=True)
        )
        nearest = None
        for candidate in candidates:
            distance = _haversine_km(
                destination.latitude, destination.longitude,
                candidate.destination.latitude, candidate.destination.longitude,
            )
            if distance is not None and (nearest is None or distance < nearest[0]):
                nearest = (distance, candidate)
        if nearest:
            baseline = nearest[1]
            baseline_match = {
                "destination": baseline.destination.name,
                "distance_km": round(nearest[0], 1),
                "method": "nearest imported baseline in district" if district_candidates else "nearest Nepal risk baseline",
            }
        elif district_candidates:
            # No exact geometry: still provide a same-district historical
            # baseline, clearly marked as non-distance-based.
            baseline = district_candidates[0]
            baseline_match = {
                "destination": baseline.destination.name,
                "distance_km": None,
                "method": "same-district baseline; destination coordinates unavailable",
            }

    if baseline:
        hazard_counts.update({
            "road_accident": baseline.accidents,
            "landslide": baseline.landslide,
            "avalanche": baseline.avalanche,
            "flood": baseline.flood,
            "earthquake": baseline.earthquake_damage,
        })

    historical_score = min(100.0, sum(SEVERITY_WEIGHT.get(i.severity, 2) for i in incidents) * 4)
    if baseline:
        historical_score = max(historical_score, min(100.0, float(baseline.tourism_risk_index or 0)))
    if feedback:
        unsafe = sum(max(0, 10 - float(f.overall_safety_rating or 0)) for f in feedback) / len(feedback)
        historical_score = min(100.0, historical_score + unsafe * 3)

    current = list(destination.current_hazards.filter(is_active=True).filter(
        Q(expires_at__isnull=True) | Q(expires_at__gte=now)
    ))

    # Existing Alert records are also current-condition inputs. Match by city /
    # district first, then use a defensible 75 km proximity window.
    nearby_alerts = []
    alert_qs = Alert.objects.filter(is_active=True).filter(Q(ends_at__isnull=True) | Q(ends_at__gte=now))
    for alert in alert_qs[:200]:
        text_match = bool(
            (alert.city and alert.city.lower() in {(destination.city or "").lower(), (destination.district or "").lower()})
        )
        distance = _haversine_km(destination.latitude, destination.longitude, alert.latitude, alert.longitude)
        if text_match or (distance is not None and distance <= 75):
            nearby_alerts.append((alert, distance))

    current_score = 0.0
    current_items = []
    for item in current:
        current_score = max(current_score, SEVERITY_WEIGHT.get(item.severity, 2) * 20)
        current_items.append({
            "id": f"hazard-{item.id}", "hazard_type": item.hazard_type,
            "title": item.title, "description": item.description, "severity": item.severity,
            "source_type": item.source_type, "source_name": item.source_name,
            "source_url": item.source_url, "published_at": item.published_at,
            "observed_at": item.observed_at, "affected_area": item.affected_area,
            "expires_at": item.expires_at, "station_name": item.station_name,
            "distance_km": item.distance_km, "verified": item.verified,
        })
    for alert, distance in nearby_alerts:
        current_score = max(current_score, SEVERITY_WEIGHT.get(alert.severity, 2) * 20)
        current_items.append({
            "id": f"alert-{alert.id}", "hazard_type": alert.alert_type,
            "title": alert.title, "description": alert.description, "severity": alert.severity,
            "source_type": "official" if alert.source else "admin",
            "source_name": alert.source or "Tourism operations",
            "source_url": "", "observed_at": alert.starts_at, "expires_at": alert.ends_at,
            "station_name": "", "distance_km": round(distance, 1) if distance is not None else None,
            "verified": bool(alert.source),
        })

    # Historical evidence is stable; active warnings dominate the current score.
    model_score = round(min(100.0, historical_score * 0.55 + current_score * 0.45), 1)
    if current_score >= 70:
        model_score = max(model_score, current_score)

    avg_feedback = feedback_qs.aggregate(value=Avg("overall_safety_rating"))["value"]
    breakdown = []
    for key, count in hazard_counts.most_common():
        if count:
            breakdown.append({
                "hazard_type": key,
                "label": HAZARD_LABELS.get(key, key.replace("_", " ").title()),
                "incident_count": count,
            })

    return {
        "destination": {
            "id": destination.id, "name": destination.name, "slug": destination.slug,
            "district": destination.district, "province": destination.province,
            "latitude": destination.latitude, "longitude": destination.longitude,
        },
        "overall": {
            "level": _level(model_score), "score": model_score,
            "label": "Model risk indicator", "is_official_warning": False,
            "explanation": "Weighted from verified history, traveler records and active observations. It is not an official forecast.",
        },
        "current_conditions": {
            "level": _level(current_score), "score": round(current_score, 1),
            "active_count": len(current_items), "items": current_items,
            "official_warning_present": any(i["source_type"] == "official" and i["verified"] for i in current_items),
        },
        "historical": {
            "level": _level(historical_score), "score": round(historical_score, 1),
            "incident_count": len(incidents), "baseline_match": baseline_match, "breakdown": breakdown,
            "timeline": [{
                "id": i.id, "event_date": i.event_date, "hazard_type": i.hazard_type,
                "title": i.title, "severity": i.severity, "source_type": i.source_type,
                "source_name": i.source_name, "source_url": i.source_url,
                "published_at": i.published_at, "affected_area": i.affected_area,
                "municipality": i.municipality, "latitude": i.latitude, "longitude": i.longitude,
                "verified": i.verified,
            } for i in incidents[:20]],
        },
        "traveler_evidence": {
            "report_count": len(feedback),
            "average_safety_rating": round(float(avg_feedback), 1) if avg_feedback is not None else None,
            "accident_reports": sum(1 for f in feedback if f.accident_occurred),
            "sickness_reports": sum(1 for f in feedback if f.became_sick),
        },
        "sources": [
            {"name": "DHM Nepal", "type": "official_reference", "url": "https://www.dhm.gov.np/", "status": "No live record" if not current_items else "See current observations"},
            {"name": "BIPAD Portal", "type": "official_reference", "url": "https://bipadportal.gov.np/", "status": "Reference source"},
            {"name": "Traveler reports", "type": "user", "url": "", "status": f"{len(feedback)} records"},
        ],
        "calculated_at": now,
        "disclaimer": "Check DHM, BIPAD and local authorities before travel. Historical incidents and model indicators are not official warnings.",
    }
