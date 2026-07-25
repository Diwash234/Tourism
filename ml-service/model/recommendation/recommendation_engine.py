import math
import os

import joblib
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# Load data
df = pd.read_csv("processed_data/destinations_clean.csv")
df = df.fillna({
    "Name": "",
    "Type": "",
    "Tourism_Category": "",
    "City": "",
    "Latitude": 0.0,
    "Longitude": 0.0,
})

# Create features
df["features"] = (
    df["Type"].astype(str).fillna("")
    + " "
    + df["Tourism_Category"].astype(str).fillna("")
    + " "
    + df["City"].astype(str).fillna("")
)


# Convert text to vectors

vectorizer = TfidfVectorizer()

destination_vectors = vectorizer.fit_transform(
    df["features"]
)


# Create output folder

os.makedirs(
    "model/recommendation",
    exist_ok=True
)


# Save model

joblib.dump(
    vectorizer,
    "model/recommendation/vectorizer.joblib"
)


joblib.dump(
    destination_vectors,
    "model/recommendation/destination_vectors.joblib"
)

destinations = pd.read_csv(
    "model/recommendation/destinations.csv")
df.to_csv(
    "model/recommendation/destinations.csv",
    index=False
)

def recommend(user_input, top_n=5):

    user_vector = vectorizer.transform([str(user_input or "")])

    similarity = cosine_similarity(
        user_vector,
        destination_vectors
    )

    indexes = similarity[0].argsort()[-top_n:][::-1]

    results = []
    for index in indexes:
        score = float(similarity[0][index])
        if not math.isfinite(score):
            score = 0.0

        row = destinations.iloc[index]
        results.append({
            "name": str(row.get("Name", "")) or "Unknown destination",
            "type": str(row.get("Type", "")),
            "category": str(row.get("Tourism_Category", "")),
            "city": str(row.get("City", "")),
            "latitude": float(row.get("Latitude", 0.0) or 0.0),
            "longitude": float(row.get("Longitude", 0.0) or 0.0),
            "score": round(score, 4),
        })

    return results


print("Recommendation model trained successfully")
