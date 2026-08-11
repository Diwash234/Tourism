"""
ML Risk & Natural Hazard Scoring Predictor for Nepal Trekking & Destinations
"""

def predict_risk(altitude: int = 1400, season: str = "autumn", district: str = "Kaski") -> dict:
    risk_score = 15.0
    advisories = []

    if altitude > 3000:
        risk_score += 25.0
        advisories.append("High altitude zone (>3000m): Acclimatization day strongly advised.")
    if altitude > 4500:
        risk_score += 30.0
        advisories.append("Extreme altitude (>4500m): Carry Diamox and monitor AMS oxygen saturation.")

    if season.lower() == "monsoon":
        risk_score += 25.0
        advisories.append("Monsoon season: Watch for highway landslides and swollen river crossings.")
    elif season.lower() == "winter":
        risk_score += 15.0
        advisories.append("Winter: High pass snow blockages and sub-zero night temperatures.")

    risk_score = min(100.0, risk_score)
    category = "LOW" if risk_score < 35 else "MODERATE" if risk_score < 70 else "HIGH"

    return {
        "altitude_m": altitude,
        "season": season,
        "district": district,
        "tourism_risk_index": round(risk_score, 1),
        "risk_category": category,
        "advisories": advisories,
        "emergency_helpline": "+977-1-4247041 (Tourist Police Nepal)"
    }
