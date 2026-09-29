# Nepal Yatra - Tourism Information Portal

A full-stack tourism platform for Nepal with Django REST API backend and React SPA frontend.

## ✨ Features

### 🏔️ Core Features
- **Destinations**: 8,500+ destinations with photos, descriptions, and reviews
- **Navigation**: GPS-based turn-by-turn navigation with offline support
- **Trip Planning**: AI-powered itinerary generation with multi-stop routing
- **Safety**: Emergency contacts, SOS alerts, and family safety features
- **Booking**: Hotel booking with real-time availability
- **Chatbot**: AI-powered travel assistant

### 🚀 Advanced Features
- **Real-time Chat**: WebSocket-based live chat with AI
- **CMS**: Full content management with draft/publish workflow
- **Multi-language**: Support for 28 languages with translation
- **Weather**: Current weather and 5-day forecast
- **Reviews**: User reviews with moderation workflow
- **Analytics**: Admin dashboard with real-time metrics
- **Media Library**: Image management with AI-powered search

### 🛠️ Technical Features
- **API**: RESTful API with OpenAPI documentation
- **Authentication**: JWT with refresh token rotation
- **Database**: PostgreSQL (production) / SQLite (development)
- **Caching**: Redis-compatible caching layer
- **Deployment**: Docker + Render ready
- **Monitoring**: Health checks and audit logging

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        React SPA                             │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │  Home   │ │ Explore │ │  Plan   │ │ Safety  │           │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Django REST API                           │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │ tourist │ │  nav    │ │ booking │ │  chat   │           │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │  admin  │ │ safety  │ │  audit  │ │  cache  │           │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     PostgreSQL                               │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │  users  │ │  dest   │ │  hotels │ │ reviews │           │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+
- PostgreSQL 16+ (optional, SQLite for dev)

### Local Development

```bash
# Clone repository
git clone https://github.com/Diwash234/Tourism.git
cd Tourism

# Backend setup
cd Tourism
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Setup database
python manage.py migrate
python manage.py install_public_seed_db
python manage.py createsuperuser

# Run backend
python manage.py runserver

# Frontend setup (new terminal)
cd ../frontend/Tourism
npm install
npm run dev
```

### Docker

```bash
# Build and run
docker-compose up --build

# Access
# Frontend: http://localhost:5173
# Backend: http://localhost:8000
# Admin: http://localhost:8000/admin
```

### Render Deployment

See [docs/RENDER_DEPLOYMENT.md](docs/RENDER_DEPLOYMENT.md) for detailed instructions.

Quick deploy:
```bash
# Prepare data
python manage.py prepare_render_data --output load.json

# Push to GitHub
git add -A
git commit -m "Deploy"
git push origin main

# Render auto-deploys
```

## 📚 Documentation

- [Deployment Guide](docs/RENDER_DEPLOYMENT.md)
- [API Documentation](http://localhost:8000/api/docs/)
- [Changelog](CHANGELOG.md)

## 🔧 Management Commands

```bash
# Data management
python manage.py prepare_render_data --output load.json
python manage.py export_render_data --output data.json
python manage.py import_render_data load.json

# Database
python manage.py backup_database
python manage.py restore_database backup.sql
python manage.py merge_duplicate_destinations

# Verification
python manage.py verify_deployment
python manage.py validate_production_config

# Data quality
python manage.py audit_data_quality
python manage.py audit_cross_place_images
python manage.py repair_real_place_images
```

## 🔒 Security

- JWT authentication with refresh token rotation
- Rate limiting on all public endpoints
- Input validation and sanitization
- CORS and CSRF protection
- HTTPS enforcement in production
- No sensitive data in logs

## 📊 Performance

- Database connection pooling (CONN_MAX_AGE=600)
- Query optimization with select_related/prefetch_related
- Caching for expensive queries
- Gzip compression
- WhiteNoise static file serving
- CDN-ready media serving

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `python manage.py test`
5. Submit a pull request

## 📄 License

MIT License

## 👥 Support

- GitHub Issues: https://github.com/Diwash234/Tourism/issues
- Email: support@nepalyatra.com
