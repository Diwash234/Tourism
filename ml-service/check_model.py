import joblib


print("Loading vectorizer...")
vectorizer = joblib.load(
    "model/recommendation/vectorizer.joblib"
)

print("Vectorizer loaded")


print("Loading destination vectors...")
vectors = joblib.load(
    "model/recommendation/destination_vectors.joblib"
)

print("Vectors loaded")
print(vectors.shape)
