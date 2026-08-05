"""
Development settings.

Run locally with:
    export DJANGO_SETTINGS_MODULE=config.settings.dev
    python manage.py runserver
"""
from .base import *  # noqa: F401,F403

# Fine to hardcode a throwaway key in dev — never used in production.
SECRET_KEY = "django-insecure-dev-only-key-do-not-use-in-production"

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# SQLite keeps local setup to zero external services.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
}

# django-debug-toolbar is intentionally NOT included by default
# (see "avoid unnecessary dependencies" project rule). Add it here
# yourself if you want it for local debugging only.
