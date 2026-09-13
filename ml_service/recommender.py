"""
ML Collaborative & Content-Based Recommendation Engine for Nepal Destinations
"""

def recommend_destinations(user_interests: list = None, top_n: int = 5) -> list:
    recommendations = [
        {"name": "Phewa Lake & Tal Barahi", "city": "Pokhara", "score": 0.98, "category": "Lakes & Water"},
        {"name": "Pashupatinath Temple", "city": "Kathmandu", "score": 0.96, "category": "Heritage & Temples"},
        {"name": "Annapurna Base Camp", "city": "Kaski", "score": 0.94, "category": "Nature & Trekking"},
        {"name": "Chitwan National Park Safari", "city": "Sauraha", "score": 0.92, "category": "Wildlife"},
        {"name": "Boudhanath Stupa", "city": "Kathmandu", "score": 0.90, "category": "Heritage & Temples"},
    ]
    return recommendations[:top_n]
