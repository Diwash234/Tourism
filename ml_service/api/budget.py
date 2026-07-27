from fastapi import APIRouter
from pydantic import BaseModel


from model.budget.budget_engine import estimate_budget



router=APIRouter()



class BudgetRequest(BaseModel):

    transport_cost:float=10

    food_cost_day:float=15

    accommodation_night:float=25

    taxi_cost:float=5

    days:int=3



@router.post("/predict-budget")
def predict_budget(
    payload:BudgetRequest
):


    return estimate_budget(

        payload.transport_cost,

        payload.food_cost_day,

        payload.accommodation_night,

        payload.taxi_cost,

        payload.days

    )

#     cd ml-service

# venv\Scripts\activate

# python training/process_budget.py

# python training/train_budget_model.py