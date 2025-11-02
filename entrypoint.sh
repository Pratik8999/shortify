#!/bin/bash
# entrypoint.sh

set -e  # exit on first error

echo "🗄️  Running database migrations..."
uv run alembic upgrade head

echo "🚀 Starting FastAPI app..."
exec "$@"
