from pathlib import Path
from dotenv import load_dotenv
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

    'shop.apps.ShopConfig',
]


# ============================================================
#  MIDDLEWARE
# ============================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
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

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/Madrid'
USE_I18N = True
USE_TZ = True


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
                "title": "Customers & Orders",
                "items": [
                    {"title": "Customers",   "icon": "person",       "link": "/admin/shop/customer/"},
                    {"title": "Orders",      "icon": "receipt_long", "link": "/admin/shop/order/"},
                    {"title": "Order Items", "icon": "checkroom",    "link": "/admin/shop/orderitem/"},
                ],
            },
            {
                "title": "Production",
                "items": [
                    {"title": "Work Tickets",       "icon": "assignment",      "link": "/admin/shop/workticket/"},
                    {"title": "Production Stages",  "icon": "timeline",        "link": "/admin/shop/productionstage/"},
                    {"title": "Measurements",       "icon": "straighten",      "link": "/admin/shop/measurement/"},
                ],
            },
            {
                "title": "Resources",
                "items": [
                    {"title": "Employees",  "icon": "badge",         "link": "/admin/shop/employee/"},
                    {"title": "Materials",  "icon": "inventory_2",   "link": "/admin/shop/material/"},
                    {"title": "Deliveries", "icon": "local_shipping","link": "/admin/shop/delivery/"},
                ],
            },
        ],
    },
}