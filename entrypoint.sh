#!/bin/sh
# WARNING: In Kubernetes with multiple replicas,
# running migrations here can cause race conditions.
# Use an init container or migration job for production environments.
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting application..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8000
