"""Destination risk aggregation with precise numerical scoring.

Historical evidence, current observations and the model indicator deliberately
remain separate.  A model score must never be presented as an official warning.
Enhanced with real-time numerical scoring, historical trends, and ML predictions.
"""
from collections import Counter, defaultdict
from datetime import timedelta
from math import atan2, cos, radians, sin, sqrt
import statistics

from django.db.models import Avg, Count, Q, Max, Min
from django.utils import timezone

from .models import Alert, CurrentHazard, RiskIncident, RiskNewsReport, RiskObservation, TravelRiskFeedback, RiskAnalysis

SEVERITY_WEIGHT = {"low": 1.0, "moderate": 2.0, "high": 3.5, "critical": 5.0}
HAZARD_LABELS = dict(RiskIncident.HazardType.choices)

# Risk categories with their impact weights.
#
# Keys MUST match RiskIncident.HazardType exactly. This table used to carry
# "wildfire", "storm", "avian_flu", "civil_unrest" and "health_outbreak" --
# names the model cannot store -- while omitting glof, heavy_rain, snowstorm,
# lightning, forest_fire and health, which it can. Consequences: GLOF (one of
# the most serious hazards in the Himalaya) was never scored, and the dead keys
# could never match a row, so category_risk could not report them at all.
#
# base_weight MULTIPLIES the severity weight rather than replacing it, so a
# "high" landslide still outranks a "low" one. It is applied in
# _calculate_precise_score.
RISK_CATEGORIES = {
    # --- Natural hazards ---
    "glof": {"base_weight": 1.6, "seasonal_peak": [6, 7, 8, 9]},          # Glacial lake outburst
    "landslide": {"base_weight": 1.5, "seasonal_peak": [6, 7, 8, 9]},
    "flood": {"base_weight": 1.4, "seasonal_peak": [6, 7, 8, 9]},
    "avalanche": {"base_weight": 1.3, "seasonal_peak": [12, 1, 2, 3]},
    "earthquake": {"base_weight": 1.2, "seasonal_peak": []},
    "forest_fire": {"base_weight": 0.9, "seasonal_peak": [3, 4, 5, 10, 11]},
    # --- Weather ---
    "heavy_rain": {"base_weight": 1.2, "seasonal_peak": [6, 7, 8, 9]},
    "snowstorm": {"base_weight": 1.1, "seasonal_peak": [12, 1, 2, 3]},
    "lightning": {"base_weight": 1.0, "seasonal_peak": [5, 6, 7, 8]},
    "extreme_weather": {"base_weight": 1.3, "seasonal_peak": [6, 7, 8, 9]},
    # --- Transport ---
    "road_accident": {"base_weight": 1.15, "seasonal_peak": [6, 7, 8, 9, 10, 11]},
    # --- Health ---
    "health": {"base_weight": 1.25, "seasonal_peak": []},
    # --- Civil / security ---
    "civil_unrest": {"base_weight": 1.3, "seasonal_peak": []},            # Protests, strikes, bandhs
    "crime": {"base_weight": 1.2, "seasonal_peak": []},
    # --- Fallback ---
    "other": {"base_weight": 0.8, "seasonal_peak": []},
}

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

def _calculate_seasonal_factor(hazard_type, month):
    """Calculate seasonal risk factor based on historical patterns."""
    if hazard_type not in RISK_CATEGORIES:
        return 1.0
    config = RISK_CATEGORIES[hazard_type]
    if month in config["seasonal_peak"]:
        return 1.5  # 50% increase during peak season
    return 1.0

def _calculate_trend(incidents, days=30):
    """Calculate risk trend over the last N days."""
    if not incidents:
        return {"direction": "stable", "change_pct": 0.0, "incidents_last_30d": 0}
    
    now = timezone.now()
    # EventIncident.event_date is a DateField, so the cutoff must be a date
    # too -- comparing a date against a datetime raises TypeError and 500s
    # the risk endpoint (same class of bug as _calculate_precise_score).
    cutoff = (now - timedelta(days=days)).date()
    recent = [i for i in incidents if i.event_date and i.event_date >= cutoff]
    older = [i for i in incidents if i.event_date and i.event_date < cutoff]
    
    recent_count = len(recent)
    older_count = len(older) if older else 1
    
    change_pct = ((recent_count - older_count) / older_count) * 100
    
    if change_pct > 20:
        direction = "increasing"
    elif change_pct < -20:
        direction = "decreasing"
    else:
        direction = "stable"
    
    return {
        "direction": direction,
        "change_pct": round(change_pct, 1),
        "incidents_last_30d": recent_count,
        "incidents_previous_30d": len(older)
    }

def _calculate_precise_score(incidents, current_hazards, feedback, baseline, destination):
    """Calculate precise numerical risk score with breakdown."""
    now = timezone.now()
    month = now.month
    
    # Historical score with seasonal adjustments
    historical_scores = []
    for incident in incidents:
        severity_weight = SEVERITY_WEIGHT.get(incident.severity, 2.0)
        hazard_config = RISK_CATEGORIES.get(incident.hazard_type, {})
        # The hazard's own impact weight MULTIPLIES the severity weight. This
        # was previously assigned to a local and then never used, so every
        # hazard scored identically for a given severity: a "high" landslide
        # and a "high" road accident contributed the same, and GLOF -- which
        # outranks almost everything here -- carried no extra weight at all.
        hazard_weight = float(hazard_config.get("base_weight", 1.0))
        base_weight = severity_weight * hazard_weight
        seasonal_factor = _calculate_seasonal_factor(incident.hazard_type, incident.event_date.month if incident.event_date else month)
        # Weight by recency (more recent = higher weight).
        # event_date is a DateField while timezone.now() returns a datetime,
        # so subtract dates — datetime - date raises TypeError and 500s the
        # whole risk endpoint for any destination that has a recorded incident.
        days_ago = (now.date() - incident.event_date).days if incident.event_date else 365
        recency_factor = max(0.1, 1.0 - (days_ago / 365.0))
        score = base_weight * seasonal_factor * recency_factor * 10
        historical_scores.append(score)
    
    historical_score = min(100.0, sum(historical_scores))
    
    # Add baseline risk index if available
    if baseline and baseline.tourism_risk_index:
        historical_score = max(historical_score, float(baseline.tourism_risk_index))
    
    # Add traveler feedback
    if feedback:
        avg_safety = sum(float(f.overall_safety_rating or 5) for f in feedback) / len(feedback)
        unsafe_factor = max(0, (5 - avg_safety) / 5) * 20  # 0-20 penalty
        historical_score = min(100.0, historical_score + unsafe_factor)
    
    # Current conditions score
    current_score = 0.0
    current_items = []
    for hazard in current_hazards:
        weight = SEVERITY_WEIGHT.get(hazard.severity, 2) * 20
        current_score = max(current_score, weight)
        current_items.append({
            "id": f"hazard-{hazard.id}", "hazard_type": hazard.hazard_type,
            "title": hazard.title, "description": hazard.description,
            "severity": hazard.severity, "source_type": hazard.source_type,
            "source_name": hazard.source_name, "source_url": hazard.source_url,
            "published_at": hazard.published_at, "observed_at": hazard.observed_at,
            "affected_area": hazard.affected_area, "expires_at": hazard.expires_at,
            "station_name": hazard.station_name, "distance_km": hazard.distance_km,
            "verified": hazard.verified,
            "numerical_score": round(weight, 1)
        })
    
    # Combined model score with precise weighting
    # Historical: 35%, Current: 45%, Seasonal/Contextual: 20%
    seasonal_context_score = 0
    if destination.latitude and destination.longitude:
        # Add elevation risk.
        # Destination.altitude is a free-text CharField (e.g. "2,175m / 7,135 ft"),
        # so comparing it to a number raises TypeError and 500s every risk /
        # emergency-services endpoint for any place with an altitude recorded.
        # Parse the text, and fall back to the DEM elevation when it is missing
        # or unreadable.
        from .elevation import best_elevation

        elevation_m = best_elevation(destination).get("elevation_m")
        if elevation_m is not None:
            if elevation_m > 4000:
                seasonal_context_score += 15
            elif elevation_m > 2500:
                seasonal_context_score += 8
        
        # Add seasonal risk based on current month
        for hazard_type in RISK_CATEGORIES:
            seasonal_context_score += _calculate_seasonal_factor(hazard_type, month) * 2
    
    model_score = round(min(100.0, historical_score * 0.35 + current_score * 0.45 + seasonal_context_score * 0.20), 1)
    
    # Blend in the admin-curated safety profile when it exists.
    # `overall_safety_score` / `travel_safety_score` are 0-100 where
    # higher = SAFER, so the risk contribution is (100 - score). The
    # curated review carries real weight (30%) because it reflects
    # verified on-the-ground facts the model has never seen.
    curated_safety = None
    if baseline is not None:
        for attr in ("overall_safety_score", "travel_safety_score"):
            value = getattr(baseline, attr, None)
            if value is not None:
                curated_safety = float(value)
                break
    if curated_safety is not None:
        risk_from_safety = min(100.0, max(0.0, 100.0 - curated_safety))
        model_score = round(min(100.0, model_score * 0.70 + risk_from_safety * 0.30), 1)
    
    # If critical current conditions, boost score
    if current_score >= 70:
        model_score = max(model_score, current_score)
    
    return {
        "model_score": model_score,
        "historical_score": round(historical_score, 1),
        "current_score": round(current_score, 1),
        "seasonal_context_score": round(seasonal_context_score, 1),
        "historical_items": historical_scores,
        "current_items": current_items
    }


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
    
    # Fetch all relevant data
    incidents = list(destination.risk_incidents.filter(is_archived=False)[:100])
    feedback_qs = TravelRiskFeedback.objects.filter(
        Q(destination=destination) | Q(destination__isnull=True, destination_name__iexact=destination.name)
    )
    feedback = list(feedback_qs[:100])
    
    # Count hazards
    hazard_counts = Counter(i.hazard_type for i in incidents)
    feedback_hazards = Counter(
        (f.hazard_witnessed or "").strip().lower().replace(" ", "_")
        for f in feedback if (f.hazard_witnessed or "").lower() != "none"
    )
    hazard_counts.update(feedback_hazards)
    
    # Get baseline
    baseline = getattr(destination, "risk_analysis", None)
    baseline_match = None
    if baseline:
        baseline_match = {"destination": destination.name, "distance_km": 0.0, "method": "exact destination"}
    else:
        from .models import RiskAnalysis
        district_candidates = list(RiskAnalysis.objects.select_related("destination").filter(
            destination__district__iexact=destination.district
        )[:250])
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
    
    # Get current hazards
    current = list(destination.current_hazards.filter(is_active=True, verified=True).filter(
        Q(expires_at__isnull=True) | Q(expires_at__gte=now)
    ))
    
    # Get nearby alerts
    nearby_alerts = []
    alert_qs = Alert.objects.filter(is_active=True, is_verified=True).filter(Q(ends_at__isnull=True) | Q(ends_at__gte=now))
    for alert in alert_qs[:200]:
        text_match = bool(
            (alert.city and alert.city.lower() in {(destination.city or "").lower(), (destination.district or "").lower()})
        )
        distance = _haversine_km(destination.latitude, destination.longitude, alert.latitude, alert.longitude)
        if text_match or (distance is not None and distance <= 75):
            nearby_alerts.append((alert, distance))
    
    # Calculate precise scores
    scores = _calculate_precise_score(incidents, current, feedback, baseline, destination)
    
    # Process current items with numerical scores
    current_items = scores["current_items"]
    for alert, distance in nearby_alerts:
        weight = SEVERITY_WEIGHT.get(alert.severity, 2) * 20
        current_items.append({
            "id": f"alert-{alert.id}", "hazard_type": alert.alert_type,
            "title": alert.title, "description": alert.description, "severity": alert.severity,
            "source_type": "official" if alert.source else "admin",
            "source_name": alert.source or "Tourism operations",
            "source_url": "", "observed_at": alert.starts_at, "expires_at": alert.ends_at,
            "station_name": "", "distance_km": round(distance, 1) if distance is not None else None,
            "verified": bool(alert.source),
            "numerical_score": round(weight, 1)
        })
    
    current_score = scores["current_score"]
    historical_score = scores["historical_score"]
    model_score = scores["model_score"]
    
    # Calculate trends
    trend = _calculate_trend(incidents)
    
    # Breakdown by hazard type with precise counts
    breakdown = []
    for key, count in hazard_counts.most_common():
        if count:
            seasonal_factor = _calculate_seasonal_factor(key, now.month)
            breakdown.append({
                "hazard_type": key,
                "label": HAZARD_LABELS.get(key, key.replace("_", " ").title()),
                "incident_count": count,
                "seasonal_factor": round(seasonal_factor, 2),
                "risk_contribution": round(count * SEVERITY_WEIGHT.get(key.split("_")[0] if "_" in key else key, 2), 1)
            })
    
    # Get observations
    observations = [{
        "id": item.id, "observation_type": item.observation_type, "value": item.value,
        "unit": item.unit, "trend": item.trend, "station_name": item.station_name,
        "station_latitude": item.station_latitude, "station_longitude": item.station_longitude,
        "distance_km": item.distance_km, "source_type": item.source_type,
        "source_name": item.source_name, "source_url": item.source_url,
        "observed_at": item.observed_at, "published_at": item.published_at,
        "verified": item.verified,
    } for item in RiskObservation.objects.filter(destination=destination, is_archived=False)[:20]]
    
    # Get verified news
    news = [{
        "id": item.id, "title": item.title, "summary": item.summary,
        "hazard_type": item.hazard_type, "source_name": item.source_name,
        "source_url": item.source_url, "published_at": item.published_at,
        "affected_area": item.affected_area, "verification_status": item.verification_status,
        "promoted_to_warning": item.promoted_to_warning,
    } for item in RiskNewsReport.objects.filter(destination=destination, verification_status="verified")[:10]]
    
    # Traveler feedback stats
    avg_feedback = feedback_qs.aggregate(value=Avg("overall_safety_rating"))["value"]
    
    # Calculate risk by category with precise scores
    category_risk = {}
    for hazard_type, config in RISK_CATEGORIES.items():
        count = hazard_counts.get(hazard_type, 0)
        if count > 0:
            # SEVERITY_WEIGHT is keyed by severity, so SEVERITY_WEIGHT.get(
            # hazard_type, 2) could never hit and always fell back to 2. Use the
            # recorded severity of these hazards instead, times the hazard's own
            # impact weight.
            type_incidents = [i for i in incidents if i.hazard_type == hazard_type]
            severities = [SEVERITY_WEIGHT.get(i.severity, 2.0) for i in type_incidents]
            severity_weight = (sum(severities) / len(severities)) if severities else 2.0
            base_score = count * float(config["base_weight"]) * severity_weight
            seasonal = _calculate_seasonal_factor(hazard_type, now.month)
            category_risk[hazard_type] = {
                "label": HAZARD_LABELS.get(hazard_type, hazard_type.replace("_", " ").title()),
                "incident_count": count,
                "base_score": round(base_score, 1),
                "seasonal_factor": round(seasonal, 2),
                "adjusted_score": round(base_score * seasonal, 1),
                "trend": _calculate_trend([i for i in incidents if i.hazard_type == hazard_type])["direction"]
            }
    
    # Overall risk level
    overall_level = _level(model_score)
    current_level = _level(current_score)
    historical_level = _level(historical_score)
    
    # Risk assessment for navigation
    navigation_risk = {
        "route_safety_score": max(0, 100 - model_score),
        "recommended": model_score < 30,
        "caution_advised": 30 <= model_score < 60,
        "avoid_recommended": model_score >= 60,
        "specific_warnings": []
    }
    
    if model_score >= 60:
        navigation_risk["specific_warnings"].append("High risk area - consider alternative routes")
    if current_score >= 50:
        navigation_risk["specific_warnings"].append("Active hazards reported in area")
    # Same CharField trap as in _calculate_precise_score: altitude is free text
    # like "2,175m / 7,135 ft" and can never be compared to a number directly.
    # This second occurrence 500'd the whole risk payload for any place with a
    # recorded altitude.
    from .elevation import best_elevation

    _nav_elevation = best_elevation(destination).get("elevation_m")
    if _nav_elevation is not None and _nav_elevation > 4000:
        navigation_risk["specific_warnings"].append("High altitude - acclimatization required")
    elif _nav_elevation is not None and _nav_elevation > 2500:
        navigation_risk["specific_warnings"].append("Altitude sickness risk above 2,500m")
    
    # Curated safety profile (admin-reviewed factors): accident
    # history, travel safety, weather exposure, emergency /
    # life-safety coverage. Surfaced so travellers see the
    # reviewed facts behind the model score.
    safety_profile = None
    if baseline is not None:
        safety_profile = {
            "travel_safety_score": baseline.travel_safety_score,
            "travel_safety_rating": baseline.travel_safety_rating,
            "overall_safety_score": baseline.overall_safety_score,
            "accident_trend": baseline.accident_trend,
            "accidents_last_year": baseline.accidents_last_year,
            "fatal_accidents_last_year": baseline.fatal_accidents_last_year,
            "accidents_last_5y": baseline.accidents_last_5y,
            "last_major_incident_date": baseline.last_major_incident_date,
            "solo_travel_safety": baseline.solo_travel_safety,
            "night_safety": baseline.night_safety,
            "family_safety": baseline.family_safety,
            "female_traveler_safety": baseline.female_traveler_safety,
            "road_quality": baseline.road_quality,
            "trail_marking": baseline.trail_marking,
            "mobile_network_coverage": baseline.mobile_network_coverage,
            "monsoon_risk": baseline.monsoon_risk,
            "winter_snow_risk": baseline.winter_snow_risk,
            "summer_heat_risk": baseline.summer_heat_risk,
            "lightning_risk": baseline.lightning_risk,
            "high_altitude_risk": baseline.high_altitude_risk,
            "uv_exposure": baseline.uv_exposure,
            "hospital_coverage": baseline.hospital_coverage,
            "emergency_response_minutes": baseline.emergency_response_minutes,
            "rescue_availability": baseline.rescue_availability,
            "medical_facility_level": baseline.medical_facility_level,
            "police_presence": baseline.police_presence,
            "risk_causes": baseline.risk_causes or [],
            "safety_summary": baseline.safety_summary,
            "last_reviewed": baseline.last_reviewed,
        }

    return {
        "destination": {
            "id": destination.id, "name": destination.name, "slug": destination.slug,
            "district": destination.district, "province": destination.province,
            "latitude": destination.latitude, "longitude": destination.longitude,
            "altitude": destination.altitude,
        },
        "overall": {
            "level": overall_level, "score": model_score,
            "label": "Model risk indicator", "is_official_warning": False,
            "explanation": "Weighted from verified history, traveler records and active observations. It is not an official forecast.",
            "confidence": "high" if len(incidents) > 5 else "medium" if len(incidents) > 0 else "low"
        },
        "navigation_risk": navigation_risk,
        "safety_profile": safety_profile,
        "current_conditions": {
            "level": current_level, "score": current_score,
            "active_count": len(current_items), "items": current_items,
            "official_warning_present": any(i["source_type"] == "official" and i["verified"] for i in current_items),
        },
        "historical": {
            "level": historical_level, "score": historical_score,
            "incident_count": len(incidents), "baseline_match": baseline_match, "breakdown": breakdown,
            "trend": trend,
            "timeline": [{
                "id": i.id, "event_date": i.event_date, "hazard_type": i.hazard_type,
                "title": i.title, "severity": i.severity, "source_type": i.source_type,
                "source_name": i.source_name, "source_url": i.source_url,
                "published_at": i.published_at, "affected_area": i.affected_area,
                "municipality": i.municipality, "latitude": i.latitude, "longitude": i.longitude,
                "verified": i.verified,
            } for i in incidents[:20]],
        },
        "category_risk": category_risk,
        "traveler_evidence": {
            "report_count": len(feedback),
            "average_safety_rating": round(float(avg_feedback), 1) if avg_feedback is not None else None,
            "accident_reports": sum(1 for f in feedback if f.accident_occurred),
            "sickness_reports": sum(1 for f in feedback if f.became_sick),
        },
        "observations": observations,
        "verified_news": news,
        "sources": [
            {"name": "DHM Nepal", "type": "official_reference", "url": "https://www.dhm.gov.np/", "status": "No live record" if not current_items else "See current observations"},
            {"name": "BIPAD Portal", "type": "official_reference", "url": "https://bipadportal.gov.np/", "status": "Reference source"},
            {"name": "Traveler reports", "type": "user", "url": "", "status": f"{len(feedback)} records"},
        ],
        "calculated_at": now,
        "disclaimer": "Check DHM, BIPAD and local authorities before travel. Historical incidents and model indicators are not official warnings.",
    }
