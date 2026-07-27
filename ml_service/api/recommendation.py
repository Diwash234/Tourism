from fastapi import APIRouter
from pydantic import BaseModel

from model.recommendation.recommendation_engine import recommend


router = APIRouter()


class RecommendationRequest(BaseModel):
    interest: str
    limit: int = 5



@router.post("/")
def recommendation(
    request: RecommendationRequest
):

    results = recommend(
        request.interest,
        request.limit
    )


    return {
        "success": True,
        "recommendations": results
    }