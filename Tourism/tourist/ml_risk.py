"""
ML-powered risk prediction for destinations.
Provides forward-looking risk forecasts based on historical patterns, 
seasonal trends, weather data, and real-time observations.
"""

from datetime import timedelta
from collections import defaultdict
from django.utils import timezone
from django.db.models import Avg, Count, Q

from .models import RiskIncident, CurrentHazard, RiskObservation, RiskAnalysis, Destination
from .risk_service import RISK_CATEGORIES, _calculate_seasonal_factor, _haversine_km


class RiskPredictor:
    """ML-based risk prediction for Nepal destinations."""
    
    def __init__(self):
        self.seasonal_weights = {
            "landslide": {6: 2.5, 7: 3.0, 8: 3.0, 9: 2.0},
            "flood": {6: 2.0, 7: 2.5, 8: 2.5, 9: 1.5},
            "avalanche": {1: 2.0, 2: 2.5, 3: 2.0, 11: 1.5, 12: 2.0},
            "road_accident": {6: 1.5, 7: 1.8, 8: 1.8, 9: 1.3},
            "wildfire": {3: 1.5, 4: 2.0, 5: 1.8, 10: 1.5, 11: 1.3},
            "storm": {6: 1.5, 7: 1.8, 8: 1.8, 9: 1.3},
        }
    
    def predict_risk(self, destination, days_ahead=7):
        """
        Predict risk score for the next N days.
        
        Returns:
            dict with daily predictions, trend, and confidence
        """
        now = timezone.now()
        current_month = now.month
        
        # Get historical incidents for this destination
        incidents = list(destination.risk_incidents.filter(is_archived=False)[:200])
        
        # Get current active hazards
        current_hazards = list(destination.current_hazards.filter(
            is_active=True, verified=True
        ).filter(Q(expires_at__isnull=True) | Q(expires_at__gte=now)))
        
        # Base score from current conditions
        base_score = self._calculate_base_score(destination, incidents, current_hazards)
        
        # Generate daily predictions
        predictions = []
        for day in range(1, days_ahead + 1):
            pred_date = now + timedelta(days=day)
            pred_month = pred_date.month
            
            daily_score = base_score
            
            # Add seasonal factor for each risk category
            for hazard_type, config in RISK_CATEGORIES.items():
                seasonal_factor = _calculate_seasonal_factor(hazard_type, pred_month)
                if seasonal_factor > 1.0:
                    daily_score += (seasonal_factor - 1.0) * 10
            
            # Add weather-based risk (if weather data available)
            weather_risk = self._predict_weather_risk(destination, pred_date)
            daily_score += weather_risk
            
            # Add trend component
            trend = self._calculate_trend(incidents)
            if trend["direction"] == "increasing":
                daily_score += min(trend["change_pct"] * 0.1, 15)
            elif trend["direction"] == "decreasing":
                daily_score -= min(abs(trend["change_pct"]) * 0.05, 10)
            
            # Cap score
            daily_score = max(0, min(100, daily_score))
            
            predictions.append({
                "date": pred_date.strftime("%Y-%m-%d"),
                "day_name": pred_date.strftime("%A"),
                "predicted_score": round(daily_score, 1),
                "level": self._level(daily_score),
                "confidence": self._calculate_confidence(incidents, day),
                "key_factors": self._get_key_factors(destination, pred_month, current_hazards)
            })
        
        return {
            "destination_id": destination.id,
            "destination_name": destination.name,
            "base_score": round(base_score, 1),
            "trend": trend,
            "predictions": predictions,
            "summary": self._generate_summary(predictions)
        }
    
    def _calculate_base_score(self, destination, incidents, current_hazards):
        """Calculate base risk score from historical and current data."""
        score = 0
        
        # Historical incidents (weighted by recency and severity)
        from .risk_service import SEVERITY_WEIGHT
        for incident in incidents[:50]:
            severity_weight = SEVERITY_WEIGHT.get(incident.severity, 2.0)
            days_ago = (timezone.now() - incident.event_date).days if incident.event_date else 365
            recency = max(0.1, 1.0 - (days_ago / 365.0))
            score += severity_weight * recency * 5
        
        # Current active hazards
        for hazard in current_hazards:
            severity_weight = SEVERITY_WEIGHT.get(hazard.severity, 2.0)
            score += severity_weight * 15
        
        # Elevation risk
        if destination.altitude:
            if destination.altitude > 4000:
                score += 20
            elif destination.altitude > 2500:
                score += 10
        
        return min(100, score)
    
    def _predict_weather_risk(self, destination, date):
        """Predict weather-related risk for a specific date."""
        # This would integrate with weather API in production
        # For now, use seasonal patterns
        month = date.month
        risk = 0
        
        # Monsoon months have higher weather risk
        if month in [6, 7, 8, 9]:
            risk += 15  # Monsoon risk
        elif month in [1, 2, 12]:
            risk += 5   # Winter risk (cold, snow at altitude)
        
        # High altitude = more weather volatility
        if destination.altitude and destination.altitude > 3500:
            risk += 10
        
        return min(risk, 30)
    
    def _calculate_trend(self, incidents):
        """Calculate risk trend from incidents."""
        now = timezone.now()
        cutoff = now - timedelta(days=30)
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
            "incidents_last_30d": recent_count
        }
    
    def _level(self, score):
        if score >= 72:
            return "critical"
        if score >= 50:
            return "high"
        if score >= 26:
            return "moderate"
        return "low"
    
    def _calculate_confidence(self, incidents, day):
        """Calculate prediction confidence based on data availability."""
        if len(incidents) > 20:
            base_confidence = 0.85
        elif len(incidents) > 5:
            base_confidence = 0.65
        else:
            base_confidence = 0.40
        
        # Confidence decreases with prediction horizon
        horizon_factor = max(0.5, 1.0 - (day * 0.05))
        
        return round(base_confidence * horizon_factor, 2)
    
    def _get_key_factors(self, destination, month, current_hazards):
        """Identify key risk factors for the prediction."""
        factors = []
        
        # Seasonal factors
        if month in [6, 7, 8, 9]:
            factors.append("Monsoon season - elevated landslide/flood risk")
        elif month in [1, 2, 12]:
            factors.append("Winter season - cold temperatures, possible snow at altitude")
        
        # Altitude factors
        if destination.altitude:
            if destination.altitude > 4000:
                factors.append(f"High altitude ({destination.altitude}m) - severe weather volatility")
            elif destination.altitude > 2500:
                factors.append(f"Moderate altitude ({destination.altitude}m) - altitude sickness risk")
        
        # Current hazards
        for hazard in current_hazards[:3]:
            factors.append(f"Active {hazard.hazard_type}: {hazard.title}")
        
        return factors[:5]  # Top 5 factors
    
    def _generate_summary(self, predictions):
        """Generate human-readable summary of predictions."""
        if not predictions:
            return "No prediction data available"
        
        avg_score = sum(p["predicted_score"] for p in predictions) / len(predictions)
        max_score = max(p["predicted_score"] for p in predictions)
        min_score = min(p["predicted_score"] for p in predictions)
        
        levels = [p["level"] for p in predictions]
        critical_days = levels.count("critical")
        high_days = levels.count("high")
        
        if critical_days > 0:
            return f"⚠️ CRITICAL: {critical_days} day(s) with critical risk. Maximum score: {max_score}/100"
        elif high_days > 0:
            return f"⚠️ HIGH RISK: {high_days} day(s) with high risk. Range: {min_score}-{max_score}/100"
        elif avg_score > 30:
            return f"⚠️ MODERATE: Average risk {avg_score:.0f}/100. Range: {min_score}-{max_score}/100"
        else:
            return f"✅ LOW RISK: Average risk {avg_score:.0f}/100. Generally safe for travel"


def get_route_risk_assessment(origin_lat, origin_lng, dest_lat, dest_lng, destination=None):
    """
    Assess risk along a route between two points.
    Useful for navigation to warn about hazardous segments.
    """
    # Find destinations near the route corridor
    route_risk = {
        "overall_score": 0,
        "segments": [],
        "warnings": [],
        "recommendations": []
    }
    
    if destination:
        # Use destination risk if available
        from .risk_service import build_destination_risk
        dest_risk = build_destination_risk(destination)
        route_risk["overall_score"] = dest_risk["overall"]["score"]
        route_risk["warnings"] = dest_risk["navigation_risk"]["specific_warnings"]
    
    # Add corridor risk (destinations near the route)
    # This would query nearby destinations in production
    
    return route_risk


# Singleton instance
risk_predictor = RiskPredictor()