# 🇳🇵 Nepal Yatra (Digital Nepal Tourism Platform)

An authentic, culturally grounded, full-stack tourism intelligence and route-planning platform for Nepal's 7 Provinces, 77 Districts, and 753 Municipalities.

Nepal Yatra combines verified geographical data, real road-network navigation, Himalayan altitude safety profiles, authentic Sherpa travel wisdom, official government permit tracking, and an authentic local guide companion (**Himal**) to empower responsible travel across Nepal.

---

## 🏛️ System Architecture

```
                          [ Client Browser / Mobile PWA ]
                                         │
                         ┌───────────────┴───────────────┐
                         │                               │
                         ▼                               ▼
                 Static Assets / PWA             Vite React SPA (Port 5173)
             (Service Worker, Offline Cache)       (2,678 Modules, Tailwind)
                         │                               │
                         └───────────────┬───────────────┘
                                         │  HTTP REST /api/v1/*
                                         ▼
                         ┌───────────────────────────────┐
                         │    Django 5.2+ REST API       │
                         │   (Business Logic, Auth,      │
                         │    RBAC, Forex, Safety, CMS)  │
                         └───────┬───────────────┬───────┘
                                 │ (Port 8000)   │ Internal HTTP (Port 8001)
                                 ▼               ▼
                      ┌──────────────────┐  ┌───────────────────────────┐
                      │    PostgreSQL    │  │   FastAPI ML Microservice │
                      │  (12k+ Records,  │  │  (Cost Regression, TF-IDF │
                      │   Public Seed)   │  │   Risk Models, Routing)   │
                      └──────────────────┘  └───────────────────────────┘
```

---

## 🚀 Quickstart: One-Command System Launch

To launch the entire platform (Dependencies ➔ Migrations ➔ ML Verification ➔ Seed ➔ Frontend ➔ Services):

```bash
chmod +x run_all.sh
./run_all.sh
```

Live Service Endpoints:
- 🌐 **Frontend SPA Website**: `http://localhost:5173`
- ⚙️ **Django Backend REST API**: `http://localhost:8000`
- 🧠 **FastAPI ML Microservice**: `http://localhost:8001`
- 📖 **API Documentation**: `http://localhost:8000/api/docs/`

---

## 🛠️ Step-by-Step Setup Guide

### 1. Prerequisites
- **Python**: 3.11 or 3.12+
- **Node.js**: 20+ (with npm 10+)
- **PostgreSQL**: 15+ (Production) or **SQLite 3** (Local Development)

---

### 2. Backend Setup (`Django REST API`)

```bash
# Navigate to the backend directory
cd Tourism

# Create and activate Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install backend dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your local settings (DEBUG=True, SECRET_KEY, etc.)

# Apply database migrations
python manage.py migrate

# Install verified public seed database (8,500+ destinations, hotels, emergency hubs)
python manage.py install_public_seed_db

# (Optional) Seed curated Himalayan signature travel itineraries
python manage.py seed_curated_travel_plans

# Create a superuser administrator
python manage.py createsuperuser

# Start Django development server
python manage.py runserver 0.0.0.0:8000
```

---

### 3. Frontend Setup (`Vite React SPA`)

```bash
# Open a new terminal and navigate to frontend directory
cd frontend/Tourism

# Install Node.js packages
npm install

# Verify production bundle build
npm run build

# Start the Vite development server
npm run dev -- --host 0.0.0.0 --port 5173
```

---

### 4. Machine Learning Microservice (`FastAPI`)

```bash
# Open a new terminal and navigate to ml_service directory
cd ml_service

# Activate virtual environment
source ../Tourism/venv/bin/activate

# Install ML dependencies (if not already installed)
pip install -r requirements.txt

# Train or verify ML model artifacts
python check_model.py

# Launch FastAPI microservice on port 8001
uvicorn app:app --host 0.0.0.0 --port 8001 --reload
```

---

## 🗄️ Database Seed & Snapshot Restore Process

The project adheres to strict **Data Honesty**: real place names, verified coordinates, Copernicus DEM elevations, and genuine administrative boundaries.

### Installing the Public Seed Snapshot
To install or reset to the verified seed database containing all destinations, official fee schedules, emergency facilities, and CMS pages:
```bash
cd Tourism
python manage.py install_public_seed_db
```
This command automatically imports `Tourism/dataset/verified_data_snapshot.json` or `load.json` and configures necessary sequences.

### Exporting & Importing Production Data
For Render / Docker deployment synchronization:
```bash
# Export the verified database to portable JSON
python manage.py export_render_data --output load.json

# Import into fresh PostgreSQL database with automatic sequence alignment
python manage.py import_render_data load.json
```

### Deployment Verification Commands
```bash
# Validate database tables, counts, and sequence synchronization
python manage.py verify_deployment

# Perform pre-flight security, SSL, and environment configuration checks
python manage.py validate_production_config
```

---

## ⚙️ Environment Variables Reference

Copy `.env.example` to `.env` in `Tourism/` and configure the following parameters:

| Variable | Default (Dev) | Description |
|---|---|---|
| `SECRET_KEY` | `django-insecure-...` | Django cryptographic secret key (Must be set in production). |
| `DEBUG` | `True` | Set to `False` in production. |
| `ALLOWED_HOSTS` | `*` | Comma-separated allowed hostnames or domains. |
| `DATABASE_URL` | `sqlite:///db.sqlite3` | Database connection string (`postgresql://user:pass@host:5432/db`). |
| `VITE_SITE_URL` | `http://localhost:5173` | Canonical origin for OpenGraph, robots.txt, and sitemap generation. |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173` | Comma-separated list of trusted frontend origins. |
| `ROUTING_BASE_URL` | _Empty_ | OSRM routing server URL (falls back cleanly to road graph or straight-line estimate). |
| `OPENWEATHER_API_KEY` | _Empty_ | OpenWeatherMap API key (degrades gracefully to "unavailable" when omitted). |
| `GEOIP_PROVIDER_URL` | _Empty_ | HTTPS GeoIP endpoint (must use HTTPS; plain HTTP is strictly blocked). |
| `ML_SERVICE_URL` | `http://127.0.0.1:8001` | URL for internal FastAPI travel budget and cost estimation microservice. |
| `EMAIL_BACKEND` | `...console.EmailBackend` | Switch to `...smtp.EmailBackend` for live SMTP delivery. |
| `EMAIL_HOST` | `smtp.gmail.com` | SMTP host for emails. |
| `EMAIL_PORT` | `587` | SMTP port (typically 587 for TLS, 465 for SSL). |
| `EMAIL_USE_TLS` | `True` | Enable TLS encryption for outgoing emails. |
| `EMAIL_HOST_USER` | _Empty_ | SMTP username/email address. |
| `EMAIL_HOST_PASSWORD` | _Empty_ | SMTP app password. |
| `GOOGLE_CLIENT_ID` / `_SECRET` | _Empty_ | Google OAuth 2.0 credentials (buttons render only when configured). |
| `GITHUB_CLIENT_ID` / `_SECRET` | _Empty_ | GitHub OAuth credentials (buttons render only when configured). |
| `GROQ_API_KEY` / `GEMINI_API_KEY` | _Empty_ | LLM provider keys for the Himal travel assistant. |

---

## 🏔️ Curated Himalayan Field Kit & Features

- **Himal Travel Companion**: Culturally authentic guide assistant grounded in local customs, altitude guidelines, and respectful trekking ethics.
- **Curated Travel Plans Studio**: 12 hand-crafted signature master itineraries (Everest Base Camp, Annapurna Circuit, Langtang Valley, Upper Mustang, Lumbini Peace Circuit, Bardia Wildlife Safari, and more) with persona-based filtering (Trekker, Cultural Seeker, Wildlife Explorer, Weekend Explorer).
- **Interactive Trail Readiness Kit**:
  - **Sherpa Trail Secrets**: Teahouse etiquette, pack animal right-of-way, mani stone clockwise passing, and prayer flag traditions.
  - **Devanagari Trail Phrasebook**: Interactive audio/pronunciation guide for essential Nepali and Sherpa phrases.
  - **Trekking Crew Tipping Calculator**: Fair wage and gratuity calculator with envelope etiquette.
  - **Offline Emergency SOS Dossier**: 1-click printable A4 / pocket field brief with traveler medical ID cards, insurance policies, and national rescue hotlines (**Tourist Police 1144**, **APF Mountain Rescue 1114**, **Nepal Police 100**, **HRA Rescue +977-1-4440292**).

---

## 🧪 Testing & Verification

Run automated test suites across all layers of the stack:

```bash
# Backend unit & regression tests
cd Tourism
python manage.py test tourist.tests_curated_plans tourist.tests_source_encoding tourist.tests_phone_quality

# Run full backend test suite
python manage.py test --noinput

# Frontend ESLint check
cd ../frontend/Tourism
npm run lint

# Frontend production build check
npm run build
```

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for complete details.

---

## 👥 Community & Support

- **Repository**: [https://github.com/Diwash234/Tourism](https://github.com/Diwash234/Tourism)
- **Documentation**: [docs/RELEASE_READINESS.md](docs/RELEASE_READINESS.md)
- **Issue Tracker**: [https://github.com/Diwash234/Tourism/issues](https://github.com/Diwash234/Tourism/issues)
