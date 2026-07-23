import pandas as pd
import joblib

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


df = pd.read_csv(
    "processed_data/destinations_clean.csv"
)


df["features"] = (
    df["Type"].fillna("")
    + " "
    + df["Tourism_Category"].fillna("")
    + " "
    + df["City"].fillna("")
)


vectorizer = TfidfVectorizer()


matrix = vectorizer.fit_transform(
    df["features"]
)


joblib.dump(
    vectorizer,
    "model/vectorizer.joblib"
)


joblib.dump(
    matrix,
    "model/destination_vectors.joblib"
)


df.to_csv(
    "model/destinations.csv",
    index=False
)


print("Training complete")
