"""
Django settings for the Tourism project (Local Tourism Information Portal).
"""
from datetime import timedelta
from pathlib import Path
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY", default="django-insecure-change-me-in-production")
DEBUG = config("DEBUG", default=True, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="*", cast=Csv())

# ------------------------------------------------------------------
# Applications
# ------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",

    # Third party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "drf_spectacular",
    "corsheaders",
    "phonenumber_field",

    # Local
    "tourist",
    "admin_panel",
    "booking",
    "chatbot",
    "safety",
    "audit",            # Audit logs + error tracking (finds mistakes)
    "system_health",    # Live diagnostics & health snapshots
    # "notifications",
    # "media_app",
    # "translations",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "audit.middleware.AuditMiddleware",   # logs every request + error to AuditLog/ErrorEvent
    "tourist.middleware.GeoIPMiddleware",
]

ROOT_URLCONF = "Tourism.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "Tourism.wsgi.application"
ASGI_APPLICATION = "Tourism.asgi.application"

# ------------------------------------------------------------------
# Database
# ------------------------------------------------------------------
# Defaults to SQLite so the project runs with zero external setup
# (good for a student/team project). Set DB_ENGINE=postgres in .env to
# switch to PostgreSQL for production without touching this file.
if config("DB_ENGINE", default="sqlite") == "postgres":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": config("DB_NAME", default="tourism_db"),
            "USER": config("DB_USER", default="tourism_user"),
            "PASSWORD": config("DB_PASSWORD", default="tourism_pass"),
            "HOST": config("DB_HOST", default="localhost"),
            "PORT": config("DB_PORT", default="5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / config("DB_NAME", default="db.sqlite3"),
        }
    }

# ------------------------------------------------------------------
# Custom user model
# ------------------------------------------------------------------
AUTH_USER_MODEL = "tourist.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ------------------------------------------------------------------
# I18N
# ------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = config("TIME_ZONE", default="UTC")
USE_I18N = True
USE_TZ = True

# ------------------------------------------------------------------
# Static & media
# ------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ---------------------------------------------------------------------------
# STANDALONE IMAGE SERVER
# ---------------------------------------------------------------------------
# Django never stores or transfers the large image dataset. The database only
# stores relative paths (DestinationImage.image_path) and the full URL is built
# from IMAGE_BASE_URL, which points at the static image server:
#   dev:   IMAGE_BASE_URL=http://localhost:8000  (python -m http.server in image-server/)
#   prod:  IMAGE_BASE_URL=https://images.example.com  (Nginx serving image-server/images/)
IMAGE_BASE_URL = config("IMAGE_BASE_URL", default="http://localhost:8000").rstrip("/")
# Local root of the image dataset (used by the import_images management command).
IMAGE_SERVER_ROOT = config(
    "IMAGE_SERVER_ROOT",
    default=str(BASE_DIR.parent / "image-server" / "images"),
)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ------------------------------------------------------------------
# Security & Headers
# ------------------------------------------------------------------
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "SAMEORIGIN"
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # Allows JS to read CSRF token if needed
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# ------------------------------------------------------------------
# CORS
# ------------------------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173",
    cast=Csv(),
)
CORS_ALLOW_CREDENTIALS = True

# ------------------------------------------------------------------
# Django REST Framework
# ------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "tourist.pagination.StandardResultsPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.ScopedRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "auth": "10/min",
        "password_reset": "5/min",
    },
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=config("ACCESS_TOKEN_LIFETIME_MIN", default=60, cast=int)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=config("REFRESH_TOKEN_LIFETIME_DAYS", default=7, cast=int)),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Local Tourism Information Portal API",
    "DESCRIPTION": "REST API for destinations, reviews, alerts, emergency info, translations and more.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

# ------------------------------------------------------------------
# Email (used for verification / password reset / notifications)
# ------------------------------------------------------------------
EMAIL_BACKEND = config(
    "EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="") 
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="no-reply@tourism-portal.local")

FRONTEND_URL = config("FRONTEND_URL", default="http://localhost:3000")

# ------------------------------------------------------------------
# SMS (Twilio) - optional, disabled unless credentials are supplied
# ------------------------------------------------------------------
TWILIO_ACCOUNT_SID = config("TWILIO_ACCOUNT_SID", default="")
TWILIO_AUTH_TOKEN = config("TWILIO_AUTH_TOKEN", default="")
TWILIO_FROM_NUMBER = config("TWILIO_FROM_NUMBER", default="")

# ------------------------------------------------------------------
# Push notifications (Firebase Cloud Messaging) - optional
# ------------------------------------------------------------------
FCM_SERVER_KEY = config("FCM_SERVER_KEY", default="")

# ------------------------------------------------------------------
# Translation (Google Translate). Falls back to the free deep-translator
# backend automatically if no API key is configured.
# ------------------------------------------------------------------
GOOGLE_TRANSLATE_API_KEY = config("GOOGLE_TRANSLATE_API_KEY", default="")
DEFAULT_LANGUAGE_CODE = config("DEFAULT_LANGUAGE_CODE", default="en")

# ------------------------------------------------------------------
# GeoIP (IP based geolocation fallback when browser GPS is unavailable)
# ------------------------------------------------------------------
GEOIP_PROVIDER_URL = config("GEOIP_PROVIDER_URL", default="http://ip-api.com/json/{ip}")

# ------------------------------------------------------------------
# Weather / Alerts external API (OpenWeatherMap etc.)
# ------------------------------------------------------------------
OPENWEATHER_API_KEY = config("OPENWEATHER_API_KEY", default="")

# ------------------------------------------------------------------
# External place/image data sources — all optional. Each client function
# in utils.py degrades gracefully (returns None / empty list) if its key
# isn't set or the service is unreachable, so the app runs fine with zero
# of these configured and gets progressively richer as you add keys.
# ------------------------------------------------------------------
# OpenStreetMap Overpass API — free, no key required, public instance by default.
OVERPASS_API_URL = config("OVERPASS_API_URL", default="https://overpass-api.de/api/interpreter")

# GeoNames — free, requires a registered username (not an API key): https://www.geonames.org/login
GEONAMES_USERNAME = config("GEONAMES_USERNAME", default="")

# Google Places API — commercial, billing required.
GOOGLE_PLACES_API_KEY = config("GOOGLE_PLACES_API_KEY", default="")

# Foursquare Places API
FOURSQUARE_API_KEY = config("FOURSQUARE_API_KEY", default="")

# Unsplash API — free tier available, used as a fallback image source when
# a destination has no user-submitted or gallery photos yet.
UNSPLASH_ACCESS_KEY = config("UNSPLASH_ACCESS_KEY", default="")
PEXELS_API_KEY = config("PEXELS_API_KEY", default="")
PIXABAY_API_KEY = config("PIXABAY_API_KEY", default="")
MAPILLARY_ACCESS_TOKEN = config("MAPILLARY_ACCESS_TOKEN", default="")

# Used by /images/resolve/ (views_images.py) to cache resolved image
# results for 7 days so repeat searches don't re-hit external APIs.
# LocMemCache needs no extra infrastructure (no Redis required) -- swap
# to django-redis later if/when Redis is deployed for other reasons.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Wikimedia Commons — free, no key required.
WIKIMEDIA_API_URL = config("WIKIMEDIA_API_URL", default="https://commons.wikimedia.org/w/api.php")

# OpenAI — used as the highest-priority translation tier (see translate_text()
# in utils.py) when configured; falls through to Google Translate, then the
# ML teammate's local-language model, then the free deep-translator library.
OPENAI_API_KEY = config("OPENAI_API_KEY", default="")
OPENAI_MODEL = config("OPENAI_MODEL", default="gpt-4o-mini")

GEMINI_API_KEY = config("GEMINI_API_KEY", default="")
GEMINI_MODEL = config("GEMINI_MODEL", default="gemini-1.5-flash")

GROQ_API_KEY = config("GROQ_API_KEY", default="")
GROQ_MODEL = config("GROQ_MODEL", default="llama-3.1-8b-instant")

# OAuth (Google / GitHub) -- read from .env, used by views_oauth.py
GOOGLE_CLIENT_ID = config("GOOGLE_CLIENT_ID", default="")
GOOGLE_CLIENT_SECRET = config("GOOGLE_CLIENT_SECRET", default="")
GITHUB_CLIENT_ID = config("GITHUB_CLIENT_ID", default="")
GITHUB_CLIENT_SECRET = config("GITHUB_CLIENT_SECRET", default="")

# Community photo promotion: once a user-submitted photo's view count
# crosses this threshold, it's automatically promoted to the destination's
# official cover image (see utils.py::maybe_promote_photo()).
PHOTO_PROMOTION_IMPRESSION_THRESHOLD = config("PHOTO_PROMOTION_IMPRESSION_THRESHOLD", default=50, cast=int)

# ------------------------------------------------------------------
# ML microservice integration (separate FastAPI/Flask service run by
# the ML teammate). The backend calls OUT to it for recommendations,
# and the ML service calls back IN (webhook) to push results.
# ------------------------------------------------------------------
ML_SERVICE_URL = config("ML_SERVICE_URL", default="http://localhost:8001")
ML_SERVICE_API_KEY = config("ML_SERVICE_API_KEY", default="change-this-ml-api-key")
ML_SERVICE_TIMEOUT = config("ML_SERVICE_TIMEOUT", default=5, cast=int)

# Optional authoritative/operational integrations. Blank means disabled; the
# application reports the integration as unconfigured rather than inventing data.
DHM_FEED_URL = config("DHM_FEED_URL", default="")
DHM_API_KEY = config("DHM_API_KEY", default="")
BIPAD_FEED_URL = config("BIPAD_FEED_URL", default="")
BIPAD_API_KEY = config("BIPAD_API_KEY", default="")
ROUTING_API_URL = config("ROUTING_API_URL", default="")
ROUTING_API_KEY = config("ROUTING_API_KEY", default="")
LOCAL_GRAPH_ROUTING_ENABLED = config("LOCAL_GRAPH_ROUTING_ENABLED", default=True, cast=bool)
LOCAL_GRAPH_MAX_SNAP_KM = config("LOCAL_GRAPH_MAX_SNAP_KM", default=100, cast=float)
EXTERNAL_SYNC_TIMEOUT = config("EXTERNAL_SYNC_TIMEOUT", default=15, cast=int)
ML_WEBHOOK_SECRET = config("ML_WEBHOOK_SECRET", default="change-this-shared-secret")
BACKEND_URL = config("BACKEND_URL", default="http://localhost:8000")
# Language codes that should try the ML teammate's local-language model
# BEFORE Google Translate (e.g. languages Google handles poorly). Populated
# automatically by `python manage.py sync_languages`, or set manually here.
LOCAL_TRANSLATION_LANGUAGE_CODES = config(
    "LOCAL_TRANSLATION_LANGUAGE_CODES", default="ne,new,mai,bho,tdg", cast=Csv()
)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "audit_db": {
            "class": "audit.logging_services.AuditDBHandler",
            "level": "WARNING",
        },
    },
    "root": {"handlers": ["console", "audit_db"], "level": "INFO"},
    "loggers": {
        "django.request": {"handlers": ["console", "audit_db"], "level": "ERROR", "propagate": False},
        "django.security": {"handlers": ["console", "audit_db"], "level": "WARNING", "propagate": False},
        "tourist": {"handlers": ["console", "audit_db"], "level": "INFO", "propagate": False},
        "audit": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}