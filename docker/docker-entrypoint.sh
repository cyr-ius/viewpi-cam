#!/bin/sh
set -euo pipefail
cd /app

# Add link media to static folder
ln -s /app/media/ /app/static/

GUNICORN_TIMEOUT="${GUNICORN_TIMEOUT:-120}"
GUNICORN_WORKERS="${GUNICORN_WORKERS:-4}"
GUNICORN_LOGLEVEL="${GUNICORN_LOGLEVEL:-info}"
BIND_ADDRESS="${BIND_ADDRESS:-0.0.0.0:8000}"
WORKER_CLASS="${WORKER_CLASS:-gthread}"
THREADS="${THREADS:-4}"

GUNICORN_ARGS="-t ${GUNICORN_TIMEOUT} --workers ${GUNICORN_WORKERS} --bind ${BIND_ADDRESS} --log-level ${GUNICORN_LOGLEVEL} --worker-class ${WORKER_CLASS} --threads ${THREADS}"

if [ "$1" == gunicorn ]; then
    # /bin/sh -c "flask db upgrade"
    exec "$@" $GUNICORN_ARGS

else
    exec "$@"
fi
