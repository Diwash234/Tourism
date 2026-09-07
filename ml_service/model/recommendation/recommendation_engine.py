import os
import math
import random
import joblib
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

MODEL_DIR = os.path.join(
    BASE_DIR,
    "model",
    "recommendation"
)
os.makedirs(MODEL_DIR, exist_ok=True)

VEC_PATH = os.path.join(MODEL_DIR, "vectorizer.joblib")
DEST_VEC_PATH = os.path.join(MODEL_DIR, "destination_vectors.joblib")
DEST_CSV_PATH = os.path.join(MODEL_DIR, "destinations.csv")

def haversine_km(lat1, lon1, lat2, lon2):
    if None in (lat1, lon1, lat2, lon2):
        return 9999.0
    try:
        r = 6371.0
        lat1, lon1, lat2, lon2 = map(math.radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2.0) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2.0) ** 2
        return 2.0 * r * math.asin(math.sqrt(a))
    except (TypeError, ValueError):
        return 9999.0

def load_or_build_model():
    if not os.path.exists(VEC_PATH) or not os.path.exists(DEST_VEC_PATH) or not os.path.exists(DEST_CSV_PATH):
        source_csv = os.path.join(BASE_DIR, "processed_data", "destinations_clean.csv")
        if not os.path.exists(source_csv):
            source_csv = os.path.join(BASE_DIR, "data", "destinations", "nepal_destinations.csv")

        if os.path.exists(source_csv):
            df = pd.read_csv(source_csv)
            for col in ["Name", "Type", "Tourism_Category", "City", "Area", "District", "Province", "search_text"]:
                if col not in df.columns:
                    df[col] = ""
                df[col] = df[col].fillna("").astype(str)

            df["features"] = (
                df["Name"] + " " + df["Type"] + " " + df["Tourism_Category"] + " " +
                df["City"] + " " + df["Area"] + " " + df["District"] + " " + df["Province"] + " " + df["search_text"]
            ).str.lower().str.replace(r"\s+", " ", regex=True).str.strip()

            vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=10000)
            d_vecs = vec.fit_transform(df["features"])

            joblib.dump(vec, VEC_PATH)
            joblib.dump(d_vecs, DEST_VEC_PATH)
            df.to_csv(DEST_CSV_PATH, index=False)
            return vec, d_vecs, df
        else:
            vec = TfidfVectorizer()
            df = pd.DataFrame([{"Name": "Everest Base Camp", "Type": "Trek", "Tourism_Category": "Nature", "City": "Solukhumbu", "Latitude": 28.0042, "Longitude": 86.8570}])
            d_vecs = vec.fit_transform(["Everest Base Camp Trek Nature Solukhumbu"])
            joblib.dump(vec, VEC_PATH)
            joblib.dump(d_vecs, DEST_VEC_PATH)
            df.to_csv(DEST_CSV_PATH, index=False)
            return vec, d_vecs, df
    else:
        vec = joblib.load(VEC_PATH)
        d_vecs = joblib.load(DEST_VEC_PATH)
        df = pd.read_csv(DEST_CSV_PATH)
        return vec, d_vecs, df

vectorizer, destination_vectors, destinations = load_or_build_model()

destinations = destinations.fillna(
    {
        "Name": "",
        "Type": "",
        "Tourism_Category": "",
        "City": "",
        "District": "",
        "Province": "",
        "Latitude": 0.0,
        "Longitude": 0.0,
    }
)


def recommend(user_input, top_n=5, user_lat=None, user_lon=None, budget_level=None, category_filter=None):
    if not user_input and not category_filter and user_lat is None:
        user_input = "nepal tourism heritage nature adventure mountain"

    try:
        # Reload vectorizer and destination dataset if updated
        global vectorizer, destination_vectors, destinations
        if os.path.exists(DEST_CSV_PATH):
            mtime = os.path.getmtime(DEST_CSV_PATH)
            if not hasattr(recommend, "_last_mtime") or recommend._last_mtime != mtime:
                vectorizer = joblib.load(VEC_PATH)
                destination_vectors = joblib.load(DEST_VEC_PATH)
                destinations = pd.read_csv(DEST_CSV_PATH).fillna({
                    "Name": "", "Type": "", "Tourism_Category": "", "City": "",
                    "District": "", "Province": "", "Latitude": 0.0, "Longitude": 0.0,
                })
                recommend._last_mtime = mtime

        query_text = str(user_input or "")
        if category_filter:
            query_text += f" {category_filter}"

        user_vector = vectorizer.transform([query_text])
        similarity = cosine_similarity(user_vector, destination_vectors)[0]

        # Calculate location proximity and category match scores
        candidates = []
        num_rows = len(destinations)

        for index in range(num_rows):
            row = destinations.iloc[index]
            sim_score = float(similarity[index])
            if not math.isfinite(sim_score):
                sim_score = 0.0

            d_lat = float(row["Latitude"]) if pd.notna(row["Latitude"]) else 0.0
            d_lon = float(row["Longitude"]) if pd.notna(row["Longitude"]) else 0.0

            dist_km = None
            prox_score = 0.0
            if user_lat is not None and user_lon is not None and d_lat != 0.0 and d_lon != 0.0:
                dist_km = round(haversine_km(user_lat, user_lon, d_lat, d_lon), 1)
                # Proximity boost for places within 100km
                if dist_km < 10.0:
                    prox_score = 0.35
                elif dist_km < 50.0:
                    prox_score = 0.25
                elif dist_km < 150.0:
                    prox_score = 0.15

            cat_str = str(row.get("Tourism_Category", row.get("Type", ""))).lower()
            cat_match = 0.15 if category_filter and category_filter.lower() in cat_str else 0.0

            final_score = round((sim_score * 0.5) + prox_score + cat_match, 4)

            # Generate preference match reasons
            reasons = []
            if sim_score > 0.1:
                reasons.append(f"✓ Matches interest in {query_text.split()[0].title()}")
            if cat_str:
                reasons.append(f"✓ Category: {row.get('Tourism_Category') or row.get('Type')}")
            if dist_km is not None and dist_km < 999:
                city_name = row.get("City") or row.get("District") or "Nepal"
                reasons.append(f"✓ {dist_km} km from your current location ({city_name})")

            candidates.append({
                "destination_id": int(row.get("ID", index + 1)),
                "name": str(row["Name"]),
                "type": str(row["Type"]),
                "category": str(row.get("Tourism_Category", row.get("Type", "Experience"))),
                "city": str(row["City"]),
                "district": str(row.get("District", "")),
                "province": str(row.get("Province", "")),
                "latitude": d_lat,
                "longitude": d_lon,
                "distance_km": dist_km,
                "similarity_score": round(sim_score, 4),
                "score": round(final_score, 4),
                "match_percentage": min(98, max(65, int(final_score * 100 + 60))),
                "match_reasons": reasons,
            })

        # Sort by combined personalized score
        candidates.sort(key=lambda x: x["score"], reverse=True)

        # Ensure diversity across cities and categories
        seen_cities = set()
        diverse_results = []
        for cand in candidates:
            city_key = (cand["city"] or cand["district"]).lower()
            if city_key not in seen_cities or len(diverse_results) < 2:
                diverse_results.append(cand)
                if city_key:
                    seen_cities.add(city_key)
            if len(diverse_results) >= top_n:
                break

        # Fallback to top candidates if diversity pool is small
        if len(diverse_results) < top_n:
            for cand in candidates:
                if cand not in diverse_results:
                    diverse_results.append(cand)
                if len(diverse_results) >= top_n:
                    break

        return diverse_results[:top_n]
    except Exception as e:
        return []
