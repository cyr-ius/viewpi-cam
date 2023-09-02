#!/bin/sh

# Assets
flask assets build

exec gunicorn --bind 0.0.0.0:8000 --workers 1 --worker-class gthread --threads 4 'app:create_app()' "$@"
