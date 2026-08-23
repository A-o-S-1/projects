"""
Base settings shared by every environment (dev, prod).

Design decision: we split settings into base/dev/prod instead of a single
settings.py so that:
  - Production secrets (SECRET_KEY, DB credentials) never live in code —
    they're read from environment variables (see prod.py).
  - Developers can run the site locally with zero config (dev.py uses
    SQLite and DEBUG=True) without risking those defaults leaking to prod.
  - Deployment simply sets DJANGO_SETTINGS_MODULE=config.settings.prod.
"""
from pathlib import Path
import os

# BASE_DIR points to the project root (school_project/), two levels up
# from this file (config/settings/base.py).
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# --------------------------------------------------------------------------
# Core apps
# --------------------------------------------------------------------------
# Our own apps live under apps/ and are added here as "apps.<name>".
# Keeping them in an apps/ package (instead of the project root) avoids
# app-name collisions with third-party packages and keeps the project
# root clean as the number of apps grows.
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",

    # Project apps (Phase 1 — public site)
    "apps.pages",
    "apps.contact",
    "apps.academics",
    "apps.staff",
    "apps.gallery",
    "apps.news_events",
    "apps.results",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise serves static files efficiently without needing Nginx to
    # know about Django's static file locations — one less moving part
    # for a small school deployment to misconfigure.
    "whitenoise.middleware.WhiteNoiseMiddleware",
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
        # Project-level templates/ holds base.html and shared partials
        # (navbar, footer). Each app also has its own templates/<app_name>/
        # folder for page-specific templates (Django's APP_DIRS below finds
        # those automatically).
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # Makes school-wide info (name, phone, address) available
                # in every template without repeating it in every view.
                "apps.pages.context_processors.school_info",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Lagos"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
}

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Sensible security defaults that apply everywhere; prod.py tightens these
# further (HTTPS-only cookies, HSTS, etc).
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = "DENY"
