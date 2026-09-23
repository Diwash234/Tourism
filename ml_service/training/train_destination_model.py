import os
import pandas as pd
import joblib

from sklearn.feature_extraction.text import TfidfVectorizer

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "processed_data", "destinations_clean.csv")
MODEL_DIR = os.path.join(BASE_DIR, "model")

os.makedirs(MODEL_DIR, exist_ok=True)

df = pd.read_csv(DATA_PATH)

df["features"] = (
    df["Type"].fillna("")
    + " "
    + df["Tourism_Category"].fillna("")
    + " "
    + df["City"].fillna("")
)

vectorizer = TfidfVectorizer()
matrix = vectorizer.fit_transform(df["features"])

joblib.dump(vectorizer, os.path.join(MODEL_DIR, "vectorizer.joblib"))
joblib.dump(matrix, os.path.join(MODEL_DIR, "destination_vectors.joblib"))
df.to_csv(os.path.join(MODEL_DIR, "destinations.csv"), index=False)

print("Training complete: destination model saved to", MODEL_DIR)
