"""
ml-service/app.py
FastAPI API gateway for the Tourism ML microservice.

This service is intentionally separate from the Django backend. Django owns
users, auth, destinations CRUD, favorites, history, etc. This service owns
anything that needs a trained model or heavier compute: risk scoring,
budget estimation, route planning, image classification, translation,
and the recommendation/chatbot logic that stitches them together.

Run locally:
    uvicorn app:app --reload --port 8001

Run in Docker: see Dockerfile.
"""
import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from api import risk, budget, routes, images, translation, recommendation, emergency

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler("logs/ml-service.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("ml-service")

app = FastAPI(
    title="Tourism ML Service",
    description="Risk, budget, route, image, translation and recommendation engine for the Tourism app.",
    version="1.0.0",
)

# The React frontend never calls this service directly in production -
# it goes through the Django backend (see README "Connecting the pieces").
# CORS is still open here for local dev / direct testing.
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://localhost:8000",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"{request.method} {request.url.path} -> {response.status_code}")
    return response


@app.get("/health")
def health():
    return {"status": "ok", "service": "ml-service"}


# Every router below is prefixed so Django's proxy view can forward
# /api/ml/<name>/... straight through with no path rewriting needed.
app.include_router(risk.router, prefix="/risk", tags=["risk"])
app.include_router(budget.router, prefix="/budget", tags=["budget"])
app.include_router(routes.router, prefix="/routes", tags=["routes"])
app.include_router(images.router, prefix="/images", tags=["images"])
app.include_router(translation.router, prefix="/translation", tags=["translation"])
app.include_router(recommendation.router, prefix="/recommendation", tags=["recommendation"])
app.include_router(emergency.router, prefix="/emergency", tags=["emergency"])