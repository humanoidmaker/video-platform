#!/bin/bash
set -e

echo "Video Platform Backend starting..."

# Run database migrations if alembic is configured
if [ -f alembic.ini ]; then
    echo "Running database migrations..."
    alembic upgrade head || echo "Migrations skipped (alembic not configured)"
fi

# Default: run the API server
if [ "$1" = "worker" ]; then
    echo "Starting Celery worker..."
    exec celery -A app.tasks.celery_app worker --loglevel=info --concurrency=4
elif [ "$1" = "beat" ]; then
    echo "Starting Celery beat..."
    exec celery -A app.tasks.celery_app beat --loglevel=info
elif [ "$1" = "flower" ]; then
    echo "Starting Flower..."
    exec celery -A app.tasks.celery_app flower --port=5555
else
    echo "Starting API server..."
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS:-2}
fi
