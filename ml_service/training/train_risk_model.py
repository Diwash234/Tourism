import os
import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score


DATA_PATH = "processed_data/risk_features.csv"
MODEL_PATH = "model/risk/risk_model.joblib"


def main():

    df = pd.read_csv(DATA_PATH)


    print("Original columns:")
    print(df.columns)


    features = [

        "accidents",
        "landslide",
        "avalanche",
        "flood",
        "earthquake_damage",
        "hospital",
        "police",
        "fire_station",
        "emergency_risk",
        "natural_disaster_risk",
        "tourism_risk_index"

    ]


    target = "risk_category"


    # Convert all feature columns to numbers
    # Anything invalid becomes NaN
    for col in features:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )


    # Replace empty values with 0
    df[features] = df[features].fillna(0)


    # Remove rows where target is missing
    df = df.dropna(
        subset=[target]
    )


    print("Rows after cleaning:", len(df))


    X = df[features]

    y = df[target]


    X_train, X_test, y_train, y_test = train_test_split(

        X,
        y,
        test_size=0.2,
        random_state=42

    )


    model = RandomForestClassifier(

        n_estimators=200,
        random_state=42

    )


    model.fit(
        X_train,
        y_train
    )


    prediction = model.predict(
        X_test
    )


    print(
        "Accuracy:",
        accuracy_score(
            y_test,
            prediction
        )
    )


    os.makedirs(
        "model/risk",
        exist_ok=True
    )


    joblib.dump(
        {
            "model": model,
            "features": features
        },
        MODEL_PATH
    )


    print(
        "Saved:",
        MODEL_PATH
    )


if __name__ == "__main__":
    main()