#!/bin/sh
set -euo pipefail
cd /app

# Add link media to static folder
ln -s -f /app/media/ /app/static/

TIMEOUT="${TIMEOUT:-120}"
WORKERS="${WORKERS:-1}"
LOGLEVEL="${LOGLEVEL:-info}"
BIND_ADDRESS="${BIND_ADDRESS:-0.0.0.0:8000}"
WORKER_CLASS="${WORKER_CLASS:-gthread}"
THREADS="${THREADS:-4}"

GUNICORN_ARGS="-t ${TIMEOUT} --workers ${WORKERS} --bind ${BIND_ADDRESS} --log-level ${LOGLEVEL} --worker-class ${WORKER_CLASS} --threads ${THREADS}"

if [ "$1" == gunicorn ]; then
    /bin/sh -c "flask db upgrade"
    exec "$@" $GUNICORN_ARGS
else
    exec "$@"
fi
