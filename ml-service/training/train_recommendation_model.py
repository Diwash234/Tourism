import pandas as pd
import joblib

from sklearn.feature_extraction.text import TfidfVectorizer


# Load data

df = pd.read_csv(
    "processed_data/destinations_clean.csv"
)


# Create feature text

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


# Save model files

joblib.dump(
    vectorizer,
    "model/recommendation/vectorizer.joblib"
)


joblib.dump(
    destination_vectors,
    "model/recommendation/destination_vectors.joblib"
)


df.to_csv(
    "model/recommendation/destinations.csv",
    index=False
)


print("Recommendation model created")
