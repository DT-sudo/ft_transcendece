from pathlib import Path

import os

from .env import env_bool, env_list, load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

# Credentials and per-deployment settings live in a git-ignored `.env` at the
# project root (see `.env.example`). Real environment variables take priority.
load_dotenv(PROJECT_ROOT / ".env")

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
DEBUG = env_bool("DEBUG", True)
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", ["localhost", "127.0.0.1"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.accounts.apps.AccountsConfig",
    "apps.frontend.apps.FrontendConfig",
    "apps.legal.apps.LegalConfig",
    "apps.scheduling.apps.SchedulingConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [PROJECT_ROOT / "frontend" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.environ.get("DB_NAME", str(BASE_DIR / "db.sqlite3")),
        "USER": os.environ.get("DB_USER", ""),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", ""),
        "PORT": os.environ.get("DB_PORT", ""),
    }
}

# Accounts are addressed by email; the model keeps `username` in sync with it,
# so both backends resolve the same user. ModelBackend stays second so the
# seeded/superuser accounts can still authenticate by username.
AUTHENTICATION_BACKENDS = [
    "apps.accounts.auth_backends.EmailBackend",
    "django.contrib.auth.backends.ModelBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = os.environ.get("TIME_ZONE", "UTC")
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"

# React/Tailwind bundle built by Vite (frontend/). Set VITE_DEV_SERVER_URL to
# http://localhost:5173 to load the modules from `npm run dev` instead.
FRONTEND_DIR = PROJECT_ROOT / "frontend"
FRONTEND_DIST_DIR = FRONTEND_DIR / "dist"
VITE_DEV_SERVER_URL = os.environ.get("VITE_DEV_SERVER_URL", "")

STATICFILES_DIRS = [FRONTEND_DIST_DIR]
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.User"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "login"

# ── TLS ─────────────────────────────────────────────────────────────────────
# nginx terminates TLS and proxies to Django over the container network, so
# Django learns the original scheme from the X-Forwarded-Proto header it sets.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

HTTPS_PORT = os.environ.get("HTTPS_PORT", "8443")

CSRF_TRUSTED_ORIGINS = env_list(
    "CSRF_TRUSTED_ORIGINS",
    [f"https://{host}:{HTTPS_PORT}" for host in ALLOWED_HOSTS if host != "*"],
)

# Cookies must never travel over plain HTTP. nginx already redirects :80 to
# :443, so this is defence in depth rather than the only guard.
SECURE_COOKIES = env_bool("SECURE_COOKIES", True)
SESSION_COOKIE_SECURE = SECURE_COOKIES
CSRF_COOKIE_SECURE = SECURE_COOKIES
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

# HSTS is only safe once TLS is definitely in place, so it stays off in DEBUG.
if not DEBUG:
    SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# ── Demo mode ───────────────────────────────────────────────────────────────
# One-click demo logins bypass password entry, so they must be explicitly
# enabled and default to off outside development.
ENABLE_DEMO_LOGIN = env_bool("ENABLE_DEMO_LOGIN", DEBUG)
