#!/bin/sh

# Assets
flask assets build

#
ln -s /app/media /app/static/media

exec gunicorn --bind 0.0.0.0:8000 --workers 1 --worker-class gthread --threads 4 'app:create_app()' "$@"
