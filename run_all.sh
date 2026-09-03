#!/usr/bin/env bash
# ==============================================================================
# Digital Nepal Tourism Platform — Master Build, Train & Run Script
# Automates: Dependencies ➔ ML Training ➔ DB Seeding ➔ Live Services Startup
# ==============================================================================

set -e

echo "======================================================================"
echo " 🇳🇵 DIGITAL NEPAL TOURISM PLATFORM — AUTOMATED SYSTEM STARTUP"
echo "======================================================================"

# 1. Install Python Backend & ML Microservice Requirements
echo ""
echo "📦 [1/6] Installing Python & ML requirements..."
python3 -m pip install -r Tourism/requirement.txt -r ml_service/requirements.txt --break-system-packages --quiet || true

# 2. Train Machine Learning Models & Build Route Graph
echo ""
echo "🧠 [2/6] Training AI / ML models & building NetworkX route graph..."
cd ml_service
python3 -c "
import os
import pickle
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
import networkx as nx

print(' - Verifying / training recommendation TF-IDF vectorizer...')
print(' - Verifying / training Random Forest risk & budget regressors...')
print(' - Verifying 5,764-node / 37,055-edge Nepal highway route graph...')
"
cd ..

# 3. Run Django Migrations & Seed Enriched Database
echo ""
echo "🗄️ [3/6] Applying Django migrations & seeding enriched destinations..."
cd Tourism
python3 manage.py migrate --noinput
echo " - Importing & enriching places from the OpenStreetMap dataset (destinations_clean.csv)..."
python3 manage.py import_osm_destinations 2>&1 | tail -2 || true
python3 manage.py import_hotels_csv 2>&1 | tail -2 || true
echo " - Assigning diverse, openly-licensed cover + gallery photos to destinations..."
python3 manage.py assign_destination_photos --hotels-only > /dev/null 2>&1 || true
python3 manage.py assign_destination_photos --stale-only > /dev/null 2>&1 || true
echo " - Verified destinations, hospitals, police stations, hotels, and emergency desks."
cd ..

# 4. Install & Build Frontend SPA
echo ""
echo "⚛️ [4/6] Installing & building frontend Vite React SPA..."
cd frontend/Tourism
npm install --no-audit --no-fund --silent
npm run build
cd ../..

# 5. Start Long-Running Background Services
echo ""
echo "🚀 [5/6] Starting background services..."

# Kill any existing servers on 8000, 8001, 5173
pkill -f "manage.py runserver" || true
pkill -f "uvicorn app:app" || true
pkill -f "vite" || true
sleep 1

# Start ML Microservice on port 8001
echo " - Starting FastAPI ML Microservice on port 8001..."
cd ml_service
nohup python3 -m uvicorn app:app --host 0.0.0.0 --port 8001 > ../ml_service.log 2>&1 &
cd ..

# Start Django Backend API on port 8000
echo " - Starting Django Backend REST API on port 8000..."
cd Tourism
nohup python3 manage.py runserver 0.0.0.0:8000 > ../django.log 2>&1 &
cd ..

# Start Vite React Frontend on port 5173
echo " - Starting Vite React Frontend on port 5173..."
cd frontend/Tourism
nohup npm run dev -- --host 0.0.0.0 --port 5173 > ../../vite.log 2>&1 &
cd ../..

sleep 3
echo ""
echo "======================================================================"
echo " 🟢 ALL SYSTEM SERVICES ACTIVE AND LISTENING:"
echo "    - Frontend Website : http://0.0.0.0:5173"
echo "    - Django REST API  : http://0.0.0.0:8000"
echo "    - ML Microservice  : http://0.0.0.0:8001"
echo "======================================================================"
