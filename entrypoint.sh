#!/bin/bash

set -e

# Print environment variables for debugging (remove in production)
echo "Environment variables:"
echo "- SECRET_KEY: ${SECRET_KEY:0:3}..."
echo "- DEBUG: $DEBUG"
echo "- DATABASE_URL: ${DATABASE_URL:0:15}..."
echo "- REDIS_URL: ${REDIS_URL:0:15}..."

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if specified in environment variables
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ]; then
    echo "Creating superuser..."
    python manage.py createsuperuser --noinput
fi

# Determine port for gunicorn
PORT=${PORT:-8000}
echo "Starting server on port $PORT..."

# Start Gunicorn
exec gunicorn ITIHub.wsgi:application --bind 0.0.0.0:$PORT --workers 4
