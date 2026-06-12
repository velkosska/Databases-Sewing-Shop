from pathlib import Path
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-sewing-shop-change-this-in-production-2025")

DEBUG = os.getenv("DEBUG", "True").lower() in ("1", "true", "yes")

ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv(
        "ALLOWED_HOSTS",
        "localhost,127.0.0.1,.railway.app,healthcheck.railway.app",
    ).split(",")
    if h.strip()
]


# ============================================================
#  INSTALLED APPS
# ============================================================

INSTALLED_APPS = [
    'unfold',
    'unfold.contrib.filters',
    'unfold.contrib.forms',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'corsheaders',
    'shop.apps.ShopConfig',
]


# ============================================================
#  MIDDLEWARE
# ============================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',   # must be after SessionMiddleware
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'


# ============================================================
#  TEMPLATES
# ============================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# ============================================================
#  DATABASE — PostgreSQL (Railway DATABASE_URL)
# ============================================================

import dj_database_url  # noqa: E402

# Railway Postgres: prefer private URL between services (no egress, same project).
_database_url = os.getenv("DATABASE_PRIVATE_URL") or os.getenv("DATABASE_URL")

if not DEBUG and not _database_url:
    raise ImproperlyConfigured(
        "No database configured. In Railway: add a PostgreSQL plugin, connect it to this service, "
        "and reference DATABASE_URL (or DATABASE_PRIVATE_URL) from the Postgres service."
    )

DATABASES = {
    'default': dj_database_url.config(
        default=_database_url or "postgres://localhost/sewing_shop",
        conn_max_age=600,
    )
}


# ============================================================
#  PASSWORD VALIDATION
# ============================================================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ============================================================
#  LOCALISATION
# ============================================================

APPEND_SLASH = False  # Next.js proxy strips trailing slashes; API URLs must match as-is

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/Madrid'
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ('en', 'English'),
    ('es', 'Español'),
]

LOCALE_PATHS = [BASE_DIR / 'locale']


# ============================================================
#  STATIC FILES
# ============================================================

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================================
#  CORS — dev + production frontend (Railway / Supabase)
# ============================================================
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
for origin in os.getenv("CORS_ALLOWED_ORIGINS", "").split(","):
    origin = origin.strip()
    if origin and origin not in CORS_ALLOWED_ORIGINS:
        CORS_ALLOWED_ORIGINS.append(origin)

_frontend_url = os.getenv("FRONTEND_URL", "").rstrip("/")
if _frontend_url and _frontend_url not in CORS_ALLOWED_ORIGINS:
    CORS_ALLOWED_ORIGINS.append(_frontend_url)

_csrf_origins = [
    o.strip() for o in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()
]
CSRF_TRUSTED_ORIGINS = _csrf_origins or list(CORS_ALLOWED_ORIGINS)
CORS_ALLOW_CREDENTIALS = True


# ============================================================
#  DJANGO UNFOLD CONFIGURATION
# ============================================================

UNFOLD = {
    "SITE_TITLE": "Sewing Shop",
    "SITE_HEADER": "Sewing Shop Management",
    "SITE_SUBHEADER": "Production & Order Tracking",
    "SITE_URL": "/",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": _("Customers & Orders"),
                "items": [
                    {"title": _("Customers"),   "icon": "person",       "link": "/admin/shop/customer/"},
                    {"title": _("Orders"),      "icon": "receipt_long", "link": "/admin/shop/order/"},
                    {"title": _("Order Items"), "icon": "checkroom",    "link": "/admin/shop/orderitem/"},
                    {"title": _("Payments"),       "icon": "payments",   "link": "/admin/shop/orderpayment/"},
                ],
            },
            {
                "title": _("Production"),
                "items": [
                    {"title": _("Work Tickets"),       "icon": "assignment",      "link": "/admin/shop/workticket/"},
                    {"title": _("Production Stages"),  "icon": "timeline",        "link": "/admin/shop/productionstage/"},
                    {"title": _("Production Logs"),   "icon": "history",         "link": "/admin/shop/orderproductionlog/"},
                    {"title": _("Measurements"),       "icon": "straighten",      "link": "/admin/shop/measurement/"},
                ],
            },
            {
                "title": _("Resources"),
                "items": [
                    {"title": _("Employees"),  "icon": "badge",         "link": "/admin/shop/employee/"},
                    {"title": _("Materials"),  "icon": "inventory_2",   "link": "/admin/shop/material/"},
                    {"title": _("Deliveries"), "icon": "local_shipping","link": "/admin/shop/delivery/"},
                ],
            },
            {
                "title": "Language / Idioma",
                "items": [
                    {
                        "title": "🇬🇧 English",
                        "icon": "language",
                        "link": "/i18n/en/?next=/admin/",
                    },
                    {
                        "title": "🇪🇸 Español",
                        "icon": "language",
                        "link": "/i18n/es/?next=/admin/",
                    },
                ],
            },
        ],
    },
}
