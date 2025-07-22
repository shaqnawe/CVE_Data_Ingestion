#!/bin/bash
set -e

# Wait for Postgres to be ready
until pg_isready -h postgres -p 5432; do
  echo "Waiting for postgres..."
  sleep 2
done

# Create tables
python create_tables.py

# Start the FastAPI server
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload