import os
import joblib


BASE=os.path.dirname(__file__)


MODEL_PATH=os.path.join(
    BASE,
    "budget_model.joblib"
)


model=joblib.load(
    MODEL_PATH
)



def estimate_budget(
    transport,
    food,
    accommodation,
    taxi,
    days
):


    daily_prediction=model.predict(
        [[
            transport,
            food,
            accommodation,
            taxi
        ]]
    )[0]


    total=daily_prediction*days


    return {

        "total_budget_usd":
            round(float(total),2),


        "daily_cost_usd":
            round(float(daily_prediction),2),


        "breakdown":{

            "transport":
                round(transport*days,2),

            "food":
                round(food*days,2),

            "accommodation":
                round(accommodation*days,2),

            "local_transport":
                round(taxi*days,2)

        }

    }