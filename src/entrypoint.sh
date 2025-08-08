#!/bin/sh
set -e

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting FastAPI app..."
exec uvicorn app.main:app --reload --workers 1 --host 0.0.0.0 --port 8000