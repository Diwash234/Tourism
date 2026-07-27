import joblib
import pandas as pd

v = joblib.load("model/recommendation/vectorizer.joblib")
dv = joblib.load("model/recommendation/destination_vectors.joblib")
df = pd.read_csv("model/recommendation/destinations.csv")

print(type(v))
print(dv.shape)
print(df.shape)