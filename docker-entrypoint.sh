#!/bin/sh
# Add link media to static folder
ln -s /app/media/ /app/static/
exec gunicorn --bind 0.0.0.0:8000 --workers 1 --worker-class gthread --threads 4 'app:create_app()' "$@"
