"""
Test-only settings — overrides the MySQL DB with SQLite so tests run
without needing CREATE DATABASE privileges on MySQL.

Usage:
    python manage.py test shop.tests --settings=config.test_settings
"""
from config.settings import *  # noqa: F401, F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test_db.sqlite3",  # noqa: F405 (BASE_DIR imported via *)
    }
}

# SQLite's TruncMonth/TruncDate work when timezone is UTC
TIME_ZONE = "UTC"
