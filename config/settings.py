from pathlib import Path
from dotenv import load_dotenv
from django.utils.translation import gettext_lazy as _
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-sewing-shop-change-this-in-production-2025")

DEBUG = True

ALLOWED_HOSTS = ['*']


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
#  DATABASE — MySQL
# ============================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME':     os.getenv('DB_NAME',     'sewing_shop'),
        'USER':     os.getenv('DB_USER',     'sewing_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'Sewing@1234'),
        'HOST':     os.getenv('DB_HOST',     'localhost'),
        'PORT':     os.getenv('DB_PORT',     '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
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

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================================
#  CORS — Allow Next.js dev server
# ============================================================
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
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
                ],
            },
            {
                "title": _("Production"),
                "items": [
                    {"title": _("Work Tickets"),       "icon": "assignment",      "link": "/admin/shop/workticket/"},
                    {"title": _("Production Stages"),  "icon": "timeline",        "link": "/admin/shop/productionstage/"},
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