# Render Deployment Guide

## Quick Start

### 1. Prerequisites
- Render account
- GitHub repository connected
- PostgreSQL database created on Render

### 2. Environment Variables

Set these in your Render service (Environment tab):

| Variable | Value | Required |
|----------|-------|----------|
| `DEBUG` | `False` | Yes |
| `SECRET_KEY` | Auto-generated | Yes |
| `ALLOWED_HOSTS` | `*` | Yes |
| `DATABASE_URL` | From Render PostgreSQL | Yes |
| `DATABASE_SSL_REQUIRE` | `true` | Yes |
| `PUBLIC_SITE_URL` | `https://your-app.onrender.com` | Yes |
| `VITE_SITE_URL` | `https://your-app.onrender.com` | Yes |
| `CSRF_TRUSTED_ORIGINS` | `https://your-app.onrender.com` | Yes |
| `CORS_ALLOWED_ORIGINS` | `https://your-app.onrender.com` | Yes |
| `IMAGE_BASE_URL` | `https://your-app.onrender.com` | No |
| `ML_SERVICE_URL` | `http://ml:8001` | No |

### 3. Database Setup

#### Option A: Automatic (Recommended)
The entrypoint.sh automatically:
1. Runs migrations
2. Checks if database is empty
3. Loads data from `load.json` if present
4. Falls back to seed database

#### Option B: Manual Data Export
```bash
# Locally, export your data
python manage.py prepare_render_data --output load.json

# Copy to server and load
scp load.json user@server:/app/Tourism/
python manage.py loaddata load.json
```

### 4. Deployment Steps

1. **Create PostgreSQL Database**
   - Dashboard → New → PostgreSQL
   - Choose region closest to your users
   - Note the internal connection string

2. **Create Web Service**
   - Dashboard → New → Web Service
   - Connect your GitHub repo
   - Set build command: `pip install -r Tourism/requirements.txt && python manage.py collectstatic --noinput`
   - Set start command: `daphne -b 0.0.0.0 -p 8000 Tourism.asgi:application`

3. **Configure Environment**
   - Add all required env vars
   - Link the PostgreSQL database

4. **Deploy**
   - Push to main branch
   - Render auto-deploys

### 5. Verification

```bash
# Check health
curl https://your-app.onrender.com/health/

# Check API
curl https://your-app.onrender.com/api/v1/config/public/

# Run deployment verification
python manage.py verify_deployment
```

## Troubleshooting

### Database is Empty
```bash
# SSH into Render shell
python manage.py verify_deployment
python manage.py prepare_render_data --output load.json
python manage.py loaddata load.json
```

### Icons Not Showing
- Check `IMAGE_BASE_URL` is set
- Verify static files: `python manage.py collectstatic --noinput`
- Check browser console for 404s on icon files

### Images Not Loading
- Verify `IMAGE_BASE_URL` points to correct URL
- Check image server is running
- Verify CORS settings

### WebSocket Not Working
- Ensure `CHANNEL_LAYERS` is configured
- Check `daphne` is running (not gunicorn)
- Verify `ws://` proxy settings

## Performance Optimization

### Enable Caching
```python
# In settings.py or via env var
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://your-redis:6379/1",
    }
}
```

### Database Connection Pooling
```python
# Already configured via CONN_MAX_AGE=600
# For pgbouncer, add to DATABASE_URL:
# postgresql://user:pass@host:5432/dbname?pgbouncer=true
```

### CDN for Static Files
```python
# Use CloudFront or Cloudflare
STATIC_URL = "https://your-cdn.cloudfront.net/static/"
MEDIA_URL = "https://your-cdn.cloudfront.net/media/"
```

## Monitoring

### Health Check Endpoint
```
GET /api/v1/health/
```

### Metrics Endpoint
```
GET /api/v1/metrics/
```

### Logs
```bash
# Render logs
render logs --service your-service-name

# Django logs
python manage.py shell -c "from audit.models import ErrorEvent; print(ErrorEvent.objects.count())"
```

## Backup & Recovery

### Backup Database
```bash
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

### Restore Database
```bash
psql $DATABASE_URL < backup_20240101.sql
```

### Backup Media Files
```bash
tar -czf media_backup_$(date +%Y%m%d).tar.gz media/
```
