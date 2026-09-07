# --- FastAPI ML microservice ---
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

COPY ml_service/requirements.txt /app/ml_service/
RUN pip install --no-cache-dir -r /app/ml_service/requirements.txt

COPY ml_service/ /app/ml_service/

WORKDIR /app/ml_service
EXPOSE 8001
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
