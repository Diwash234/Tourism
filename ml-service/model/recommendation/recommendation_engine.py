import pandas as pd
import joblib
import os

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity



# Load data

df = pd.read_csv(
    "processed_data/destinations_clean.csv"
)


# Create features

df["features"] = (
    df["Type"].fillna("")
    + " "
    + df["Tourism_Category"].fillna("")
    + " "
    + df["City"].fillna("")
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

    user_vector = vectorizer.transform(
        [user_input]
    )

    similarity = cosine_similarity(
        user_vector,
        destination_vectors
    )

    indexes = similarity[0].argsort()[-top_n:][::-1]

    results = []

    for index in indexes:

        results.append({
            "name": destinations.iloc[index]["Name"],
            "type": destinations.iloc[index]["Type"],
            "category": destinations.iloc[index]["Tourism_Category"],
            "city": destinations.iloc[index]["City"],
            "latitude": destinations.iloc[index]["Latitude"],
            "longitude": destinations.iloc[index]["Longitude"],
            "score": float(similarity[0][index])
        })

    return results


print("Recommendation model trained successfully")
