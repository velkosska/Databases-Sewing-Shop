import os

# Railway injects PORT; fall back to 8080 for local gunicorn runs.
bind = f"0.0.0.0:{os.environ.get('PORT', '8080')}"
workers = 2
timeout = 120
accesslog = "-"
errorlog = "-"
