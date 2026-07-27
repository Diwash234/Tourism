import os
import pandas as pd
import joblib

from sklearn.feature_extraction.text import TfidfVectorizer


# ==============================
# Project base directory
# ==============================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


# ==============================
# Input dataset
# ==============================

DATA_FILE = os.path.join(
    BASE_DIR,
    "processed_data",
    "destinations_clean.csv"
)


# ==============================
# Model output directory
# ==============================

MODEL_DIR = os.path.join(
    BASE_DIR,
    "model",
    "recommendation"
)


os.makedirs(
    MODEL_DIR,
    exist_ok=True
)


# ==============================
# Load data
# ==============================

df = pd.read_csv(DATA_FILE)


print("==========================")
print("Loaded destinations:")
print(df.head())
print("==========================")

print("Dataset shape:")
print(df.shape)


# ==============================
# Fill missing values
# ==============================

text_columns = [
    "Name",
    "Type",
    "Tourism_Category",
    "City",
    "Area",
    "District",
    "Province",
    "search_text"
]


for col in text_columns:
    if col not in df.columns:
        df[col] = ""

    df[col] = df[col].fillna("").astype(str)



# ==============================
# Create recommendation features
# ==============================

df["features"] = (
    df["Name"] + " "
    + df["Type"] + " "
    + df["Tourism_Category"] + " "
    + df["City"] + " "
    + df["Area"] + " "
    + df["District"] + " "
    + df["Province"] + " "
    + df["search_text"]
)


# Clean spaces

df["features"] = (
    df["features"]
    .str.lower()
    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
)


print("==========================")
print("Sample features:")
print(df["features"].head())
print("==========================")


# ==============================
# TF-IDF Vectorization
# ==============================

vectorizer = TfidfVectorizer(
    stop_words="english",
    ngram_range=(1, 2),
    max_features=10000
)


destination_vectors = vectorizer.fit_transform(
    df["features"]
)


print("Vector shape:")
print(destination_vectors.shape)


print("Vocabulary size:")
print(len(vectorizer.vocabulary_))


# ==============================
# Save vectorizer
# ==============================

joblib.dump(
    vectorizer,
    os.path.join(
        MODEL_DIR,
        "vectorizer.joblib"
    )
)


# ==============================
# Save destination vectors
# ==============================

joblib.dump(
    destination_vectors,
    os.path.join(
        MODEL_DIR,
        "destination_vectors.joblib"
    )
)


# ==============================
# Save destination data
# ==============================

df.to_csv(
    os.path.join(
        MODEL_DIR,
        "destinations.csv"
    ),
    index=False
)


print("==========================")
print("Recommendation model created successfully")
print("==========================")