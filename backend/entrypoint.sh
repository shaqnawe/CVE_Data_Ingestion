#!/bin/bash
set -e

# Wait for Postgres to be ready
echo "Waiting for Postgres..."
while ! nc -z postgres 5432; do
  sleep 1
done

# Create tables
echo "Creating tables if they do not exist..."
python create_tables.py

# Start the FastAPI server
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload