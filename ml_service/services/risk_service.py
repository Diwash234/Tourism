import joblib
import os


MODEL_PATH="model/risk/risk_model.joblib"


model_data=joblib.load(
    MODEL_PATH
)


model=model_data["model"]
encoder=model_data["encoder"]



def predict_risk(data):

    values=[

        data["accidents"],
        data["landslide"],
        data["avalanche"],
        data["flood"],
        data["earthquake_damage"],
        data["hospital"],
        data["police"],
        data["fire_station"],
        data["tourism_risk_index"]

    ]


    result=model.predict(
        [values]
    )[0]


    category=encoder.inverse_transform(
        [result]
    )[0]


    return {
        "risk_category":category
    }