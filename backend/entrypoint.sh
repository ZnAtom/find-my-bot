#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
until PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c '\q' 2>/dev/null; do
  sleep 1
done

echo "PostgreSQL is ready. Running schema..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -f /app/schema.sql

echo "Running auth migration..."
python /app/migrate_auth.py

echo "Running item state migration..."
python /app/migrate_item_state.py

echo "Running flow fields migration..."
python /app/migrate_flow_fields.py

echo "Starting FastAPI..."
exec uvicorn app:app --host 0.0.0.0 --port 8000
