import os

# PORT is set explicitly to 8000 in Railway Variables (Databases-Sewing-Shop service).
# Railway Networking domain must target the same port (8000).
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
workers = 2
timeout = 120
accesslog = "-"
errorlog = "-"
