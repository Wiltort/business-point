#!/bin/sh
set -e

echo "Running Alembic migrations..."
alembic upgrade head

# Заполнение базы тестовыми данными
python -m app.scripts.populate_db

echo "Starting FastAPI app..."
exec uvicorn app.main:app --reload --workers 1 --host 0.0.0.0 --port 8000