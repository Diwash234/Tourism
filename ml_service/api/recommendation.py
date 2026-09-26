from typing import List, Optional, Union, Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from model.recommendation.recommendation_engine import recommend

router = APIRouter()

# Bounds on the request payload. Without them a client could ask for an
# unbounded result count or push an arbitrarily large `destinations` array,
# which is pure wasted work and memory on a single-process service.
MAX_RESULTS = 50
MAX_DESTINATIONS = 100
MAX_INTEREST_LENGTH = 200


class RecommendationRequest(BaseModel):
    interest: Optional[Union[str, List[str]]] = Field(
        default=None, max_length=MAX_INTEREST_LENGTH
    )
    interests: Optional[List[str]] = Field(default=None, max_length=20)
    category: Optional[str] = Field(default=None, max_length=MAX_INTEREST_LENGTH)
    limit: Optional[int] = Field(default=None, ge=1, le=MAX_RESULTS)
    top_n: Optional[int] = Field(default=None, ge=1, le=MAX_RESULTS)
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    user_id: Optional[int] = None
    destinations: Optional[List[Any]] = Field(default=None, max_length=MAX_DESTINATIONS)


@router.post("")
@router.post("/")
def recommendation(request: RecommendationRequest):
    # Extract query terms
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

    results = recommend(
        user_input=query,
        top_n=count,
        user_lat=request.latitude,
        user_lon=request.longitude,
        category_filter=request.category,
    )

    return {
        "success": True,
        "recommendations": results,
        "results": results,
    }
