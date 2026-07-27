import os
import math

import joblib
import pandas as pd

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


# Load trained files

vectorizer = joblib.load(
    os.path.join(
        MODEL_DIR,
        "vectorizer.joblib"
    )
)


destination_vectors = joblib.load(
    os.path.join(
        MODEL_DIR,
        "destination_vectors.joblib"
    )
)


destinations = pd.read_csv(
    os.path.join(
        MODEL_DIR,
        "destinations.csv"
    )
)


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



def recommend(
    user_input,
    top_n=5
):

    """
    Example:

    recommend("museum")
    recommend("lake pokhara")
    recommend("mountain trekking")
    recommend("historical temple")

    """


    if not user_input:
        return []


    # Convert user search into vector

    user_vector = vectorizer.transform(
        [
            str(user_input)
        ]
    )


    # Calculate similarity

    similarity = cosine_similarity(
        user_vector,
        destination_vectors
    )


    # Get highest scores

    indexes = (
        similarity[0]
        .argsort()
        [-top_n:]
        [::-1]
    )


    results=[]


    for index in indexes:

        score=float(
            similarity[0][index]
        )


        if not math.isfinite(score):
            score=0.0



        row = destinations.iloc[index]


        results.append(
            {

            "name":
                str(row["Name"]),


            "type":
                str(row["Type"]),


            "category":
                str(row["Tourism_Category"]),


            "city":
                str(row["City"]),


            "latitude":
                float(row["Latitude"]),


            "longitude":
                float(row["Longitude"]),


            "similarity_score":
                round(score,4)

            }
        )


    return results


    # python training/preprocess/clean_destinations.py
    # python training/train_recommendation_model.py
    # ml-service/test_recommendation.py
    # python test_recommendation.py