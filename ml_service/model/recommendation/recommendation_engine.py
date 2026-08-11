import os
import math

import joblib
import pandas as pd
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

# Auto-train if missing
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

        vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=10000)
        destination_vectors = vectorizer.fit_transform(df["features"])

        joblib.dump(vectorizer, VEC_PATH)
        joblib.dump(destination_vectors, DEST_VEC_PATH)
        df.to_csv(DEST_CSV_PATH, index=False)
        destinations = df
    else:
        vectorizer = TfidfVectorizer()
        destinations = pd.DataFrame([{"Name": "Everest Base Camp", "Type": "Trek", "Tourism_Category": "Nature", "City": "Solukhumbu", "Latitude": 28.0042, "Longitude": 86.8570}])
        destination_vectors = vectorizer.fit_transform(["Everest Base Camp Trek Nature Solukhumbu"])
        joblib.dump(vectorizer, VEC_PATH)
        joblib.dump(destination_vectors, DEST_VEC_PATH)
        destinations.to_csv(DEST_CSV_PATH, index=False)
else:
    vectorizer = joblib.load(VEC_PATH)
    destination_vectors = joblib.load(DEST_VEC_PATH)
    destinations = pd.read_csv(DEST_CSV_PATH)

destinations = destinations.fillna(
    {
        "Name": "",
        "Type": "",
        "Tourism_Category": "",
        "City": "",
        "Latitude": 0.0,
        "Longitude": 0.0,
    }
)


def recommend(user_input, top_n=5):
    if not user_input:
        return []

    try:
        user_vector = vectorizer.transform([str(user_input)])
        similarity = cosine_similarity(user_vector, destination_vectors)
        indexes = similarity[0].argsort()[-top_n:][::-1]

        results = []
        for index in indexes:
            score = float(similarity[0][index])
            if not math.isfinite(score):
                score = 0.0

            row = destinations.iloc[index]
            results.append({
                "name": str(row["Name"]),
                "type": str(row["Type"]),
                "category": str(row["Tourism_Category"]),
                "city": str(row["City"]),
                "latitude": float(row["Latitude"]) if pd.notna(row["Latitude"]) else 0.0,
                "longitude": float(row["Longitude"]) if pd.notna(row["Longitude"]) else 0.0,
                "similarity_score": round(score, 4),
            })
        return results
    except Exception as e:
        return []
