from typing import List, Optional, Union, Any
from fastapi import APIRouter
from pydantic import BaseModel

from model.recommendation.recommendation_engine import recommend

router = APIRouter()


class RecommendationRequest(BaseModel):
    interest: Optional[Union[str, List[str]]] = None
    interests: Optional[List[str]] = None
    limit: Optional[int] = None
    top_n: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    user_id: Optional[int] = None
    destinations: Optional[List[Any]] = None


@router.post("")
@router.post("/")
def recommendation(request: RecommendationRequest):
    # Extract query text
    query_terms = []
    if request.interest:
        if isinstance(request.interest, list):
            query_terms.extend([str(i) for i in request.interest if i])
        else:
            query_terms.append(str(request.interest))
    if request.interests:
        query_terms.extend([str(i) for i in request.interests if i])
    
    query = " ".join(query_terms) if query_terms else "nepal tourism heritage nature mountain"
    count = request.top_n or request.limit or 5

    results = recommend(query, top_n=count)
    return {
        "success": True,
        "recommendations": results,
        "results": results,
    }
