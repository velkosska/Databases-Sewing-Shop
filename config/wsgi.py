import os

import config  # noqa: F401 — PyMySQL shim before Django loads DB backend

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()
