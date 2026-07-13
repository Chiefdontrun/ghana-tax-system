"""
Django settings for ghana-tax-system backend.
All secrets and environment-specific values are loaded via python-decouple.
MongoDB is used directly via PyMongo — Django ORM is NOT used for primary data.
"""

import os
import warnings
from pathlib import Path
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

# ─── Security ─────────────────────────────────────────────────────────────────
SECRET_KEY = config("DJANGO_SECRET_KEY", default="unsafe-dev-secret-key-change-in-prod")
DEBUG = config("DJANGO_DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1,.vercel.app", cast=Csv())
if os.environ.get("VERCEL_URL"):
    ALLOWED_HOSTS.append(os.environ["VERCEL_URL"])

# ─── Application definition ───────────────────────────────────────────────────
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "corsheaders",
    "django_ratelimit",
    # Local apps
    "apps.auth_app",
    "apps.registration",
    "apps.tin",
    "apps.reports",
    "apps.audit",
    "apps.ussd",
    "apps.notifications",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.audit_middleware.AuditMiddleware",
]

ROOT_URLCONF = "core.urls"
WSGI_APPLICATION = "core.wsgi.application"

# ─── No Django ORM database (MongoDB via PyMongo) ─────────────────────────────
# We keep a minimal sqlite config only so Django management commands don't break.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ─── MongoDB (primary data store) ─────────────────────────────────────────────
MONGO_URI = config("MONGO_URI", default="mongodb://localhost:27017/ghana_tax_db")
_MONGO_DB_NAME = config("MONGO_DB_NAME", default="ghana_tax_db", cast=str).strip()
MONGO_DB_NAME = _MONGO_DB_NAME.lstrip("/")

# ─── Redis ────────────────────────────────────────────────────────────────────
REDIS_URL = config("REDIS_URL", default="redis://localhost:6379/0")

# ─── Cache (Redis) ────────────────────────────────────────────────────────────
# Used by reports summary endpoint for 30-60s TTL caching.
# Falls back gracefully: if Redis is unavailable or unreachable.
_USE_REDIS_CACHE = config("USE_REDIS_CACHE", default=True, cast=bool)
_REDIRECT_TO_LOCAL_CACHE = False
if _USE_REDIS_CACHE:
    try:
        import redis as _redis

        _redis.Redis.from_url(
            REDIS_URL,
            socket_connect_timeout=2,
            socket_timeout=2,
        ).ping()
    except Exception as exc:
        _REDIRECT_TO_LOCAL_CACHE = True
        # When Redis is unavailable, fallback to local in-memory cache so
        # rate limiting and reports still work without crashing the login flow.
        warnings.warn(
            f"Redis cache unreachable at {REDIS_URL}. Falling back to LocMemCache. Error: {exc}",
            RuntimeWarning,
        )

if _USE_REDIS_CACHE and not _REDIRECT_TO_LOCAL_CACHE:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
            "KEY_PREFIX": "ghana_tax",
            "TIMEOUT": 60,  # Default TTL: 60 seconds
        }
    }
    RATELIMIT_ENABLE = True
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
            "KEY_PREFIX": "ghana_tax",
            "TIMEOUT": 60,
        }
    }
    RATELIMIT_ENABLE = False

# Reports summary cache TTL (seconds) — configurable via env (spec: 30-60s)
REPORTS_CACHE_TTL = config("REPORTS_CACHE_TTL", default=45, cast=int)

# ─── JWT ──────────────────────────────────────────────────────────────────────
JWT_SECRET_KEY = config("JWT_SECRET_KEY", default="unsafe-jwt-secret-change-in-prod")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = config("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", default=60, cast=int)
JWT_REFRESH_TOKEN_EXPIRE_DAYS = config("JWT_REFRESH_TOKEN_EXPIRE_DAYS", default=7, cast=int)

# ─── Email ────────────────────────────────────────────────────────────────────
EMAIL_BACKEND = config(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend" if DEBUG else "django.core.mail.backends.smtp.EmailBackend",
)
EMAIL_HOST = config("EMAIL_HOST", default="localhost")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
DEFAULT_FROM_EMAIL = config(
    "DEFAULT_FROM_EMAIL",
    default="Ghana Tax System <no-reply@yourdomain.com>",
)
RESEND_API_KEY = config("RESEND_API_KEY", default="")

# ─── Africa's Talking ─────────────────────────────────────────────────────────
AT_API_KEY = config("AT_API_KEY", default="")
AT_USERNAME = config("AT_USERNAME", default="")
AT_SENDER_ID = config("AT_SENDER_ID", default="GH-REVENUE")

# ─── Seed data ────────────────────────────────────────────────────────────────
SEED_ADMIN_EMAIL = config("SEED_ADMIN_EMAIL", default="sysadmin@demo.gov.gh")
SEED_ADMIN_PASSWORD = config("SEED_ADMIN_PASSWORD", default="DemoPass123!")

# ─── Django REST Framework ────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.auth_app.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "EXCEPTION_HANDLER": "core.utils.response.custom_exception_handler",
}

# ─── CORS ─────────────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:5173,http://localhost:3000",
    cast=Csv(),
)
CORS_ALLOWED_ORIGIN_REGEXES = config(
    "CORS_ALLOWED_ORIGIN_REGEXES",
    default=r"^https://.*\.vercel\.app$",
    cast=Csv(),
)
CORS_ALLOW_CREDENTIALS = True

# ─── Templates (minimal — needed for Django internals) ────────────────────────
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
            ],
        },
    },
]

# ─── Internationalization ─────────────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Accra"
USE_I18N = True
USE_TZ = True

# ─── Static files ─────────────────────────────────────────────────────────────
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ─── Logging ──────────────────────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} — {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}
