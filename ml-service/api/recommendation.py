from fastapi import APIRouter
from pydantic import BaseModel

from model.recommendation.recommendation_engine import recommend


router = APIRouter()


class Request(BaseModel):
    interest:str



@router.post("/")
def recommendation(
    request:Request
):

    result = recommend(
        request.interest
    )

    return {
        "recommendations":result
    }
