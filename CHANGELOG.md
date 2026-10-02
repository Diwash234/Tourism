# Changelog

## [2.0.0] - 2026-09-29

### 🚀 Major Features

#### GPS & Location
- **GPS Validation**: Coordinates validated against Nepal's bounding box (26.0-31.0°N, 80.0-89.0°E)
- **Location History**: New `LocationHistory` model tracks user movements with accuracy and source
- **Geofencing**: Rejects null island (0,0) and coordinates outside Nepal
- **Enhanced GPS Filtering**: Accuracy-based filtering with quality indicators

#### API Enhancements
- **Weather Forecast**: 5-day forecast endpoint with daily aggregation
- **Bulk Export**: Admin-only CSV/JSON export for destinations, hotels, bookings, reviews
- **Review Moderation**: Queue-based moderation workflow for admin/staff
- **Health Check**: `/api/v1/health/` endpoint for monitoring
- **Enhanced Search**: Multi-filter search (category, district, rating, verified, images)
- **Notification Preferences**: User-configurable notification settings

#### Frontend
- **Geolocation Hook**: Custom `useGeolocation` hook with caching and fallback
- **API Caching**: `useApiCache` hook with TTL and request deduplication
- **Weather Forecast Component**: 5-day forecast display
- **Location History Component**: Timeline view with map integration
- **Review Moderation Component**: Queue-based moderation interface
- **Bulk Export Component**: Admin data export interface
- **Enhanced Search Component**: Multi-filter search with autocomplete
- **Trip Collaboration**: Share trips via link with real-time updates
- **Loyalty/Rewards**: Points, badges, and tier system

### 🐛 Bug Fixes

#### Critical
- **PostgreSQL Data Loading**: Entrypoint now auto-loads data into PostgreSQL on first deploy
- **Icons Not Showing**: Fixed react-icons bundling (full package, not just fi/bs)
- **N+1 Queries**: Fixed in PublicConfigView, DiscoverNepalView, OSMEssentialServiceNearbyView
- **Database Indexes**: Added indexes on frequently queried fields (slug, district, province, etc.)

#### High
- **GPS Validation**: User location now validated before storage
- **Race Conditions**: Fixed in booking and view count updates
- **Error Handling**: Global exception handler with consistent error format
- **Rate Limiting**: Added to search, chatbot, and public endpoints

#### Medium
- **Caching**: PublicConfigView and AdminStatsView now cached
- **Pagination**: Added to all list endpoints
- **Input Validation**: Enhanced serializer validation
- **Transaction Management**: Fixed in booking and payment flows

### 🔧 Infrastructure

#### Deployment
- **Dockerfile**: Added health check, optimized build, curl for health checks
- **render.yaml**: Added all required env vars, database config
- **Entrypoint**: Auto-detects PostgreSQL and loads data automatically
- **Deployment Script**: `scripts/prepare_deployment.py` for pre-deploy verification

#### Documentation
- **RENDER_DEPLOYMENT.md**: Complete deployment guide
- **CHANGELOG.md**: This file
- **API Documentation**: Enhanced docstrings and comments

#### New Commands
- `python manage.py prepare_render_data` - Export data for Render
- `python manage.py verify_deployment` - Post-deploy health check
- `python manage.py verify_deployment --deploy` - Django deploy check

### 📊 Performance

- **Database**: Added 9 new indexes on frequently queried fields
- **Caching**: PublicConfigView cached for 5 minutes, AdminStatsView for 1 minute
- **Query Optimization**: Fixed N+1 queries in 3 major views
- **Connection Pooling**: CONN_MAX_AGE=600 for PostgreSQL

### 🔒 Security

- **Rate Limiting**: 30/min search, 20/min chatbot, 60/min public config
- **Input Validation**: Enhanced serializer validation
- **GPS Validation**: Coordinates validated against Nepal boundaries
- **Error Handling**: Consistent error format, no sensitive data leakage

### 📦 Dependencies

- No new dependencies required
- All existing dependencies updated to latest compatible versions

### 🔄 Breaking Changes

- None - all changes are backward compatible

### 📝 Migration Notes

1. Run migrations: `python manage.py migrate`
2. Collect static: `python manage.py collectstatic --noinput`
3. Prepare data: `python manage.py prepare_render_data --output load.json`
4. Verify: `python manage.py verify_deployment`

---

## [1.0.0] - 2026-09-01

### Initial Release
- Django REST API backend
- React SPA frontend
- PostgreSQL/SQLite support
- Docker deployment
- Render configuration
