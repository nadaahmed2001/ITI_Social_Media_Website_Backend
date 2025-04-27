#!/bin/bash

set -e

echo "Starting entrypoint script..."

# Print environment variables for debugging (remove in production)
echo "Environment variables:"
echo "- SECRET_KEY: ${SECRET_KEY:0:3}..."
echo "- DEBUG: $DEBUG"
echo "- DATABASE_URL present: $([ -n "$DATABASE_URL" ] && echo 'Yes' || echo 'No')"
echo "- REDIS_URL present: $([ -n "$REDIS_URL" ] && echo 'Yes' || echo 'No')"
echo "- Current working directory: $(pwd)"

# Copy the .env file from project root to ITIHub directory if it doesn't exist
if [ -f /app/.env ] && [ ! -f /app/ITIHub/.env ]; then
    echo "Copying .env file from /app/.env to /app/ITIHub/.env"
    cp /app/.env /app/ITIHub/.env
fi

# Navigate to the directory containing manage.py
echo "Current directory before cd: $(pwd)"
cd /app/ITIHub
echo "Changed to directory: $(pwd)"
echo "Listing directory contents:"
ls -la

# Make sure DATABASE_URL is accessible in the Django environment
if [ -n "$DATABASE_URL" ]; then
    echo "DATABASE_URL is set in the environment"
    echo "DATABASE_URL starts with: ${DATABASE_URL:0:20}..."
    # Export it again to make sure it's accessible
    export DATABASE_URL
else
    echo "WARNING: DATABASE_URL is NOT set in the environment!"
    
    # Try to get it from .env file
    if [ -f .env ]; then
        echo "Trying to read DATABASE_URL from .env file"
        export DATABASE_URL=$(grep DATABASE_URL .env | cut -d '=' -f2- | sed 's/^[ \t]*//;s/[ \t]*$//')
        echo "Found DATABASE_URL in .env: ${DATABASE_URL:0:20}..."
    else
        echo "No .env file found!"
    fi
fi

# Wait for database to be ready
echo "Waiting for database to be ready..."
python -c "
import sys
import time
import psycopg2
from urllib.parse import urlparse
import os

# Parse DATABASE_URL
db_url = os.environ.get('DATABASE_URL', '')
if not db_url:
    print('DATABASE_URL not set, skipping database check')
    sys.exit(1)

print(f'Using database URL: {db_url[:20]}...')

# Parse connection parameters from the URL
result = urlparse(db_url)
dbname = result.path[1:]
user = result.username
password = result.password
host = result.hostname
port = result.port or 5432

print(f'Connecting to: {host}:{port}/{dbname} as {user}')

# Try to connect to the database
retries = 10
while retries > 0:
    try:
        print(f'Attempting to connect to database {dbname} on {host}:{port} as {user}...')
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port,
            sslmode='require'
        )
        conn.close()
        print('Database connection successful!')
        sys.exit(0)
    except psycopg2.OperationalError as e:
        print(f'Database connection failed: {e}')
        retries -= 1
        if retries > 0:
            print(f'Retrying in 5 seconds... ({retries} attempts remaining)')
            time.sleep(5)
        else:
            print('Max retries reached. Could not connect to database.')
            sys.exit(1)
"

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if specified in environment variables
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ]; then
    echo "Creating superuser..."
    python manage.py createsuperuser --noinput || echo "Superuser may already exist."
fi

# Determine port for server
PORT=${PORT:-8000}
echo "Starting server on port $PORT..."

# Add a health check endpoint
echo "Creating health check endpoint..."
mkdir -p /app/ITIHub/health/
cat > /app/ITIHub/health/views.py << 'EOF'
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({"status": "healthy"})
EOF

# Check if we should run with WebSocket support
if [ "${ENABLE_WEBSOCKET:-true}" = "true" ]; then
    echo "Starting Daphne server with WebSocket support..."
    exec daphne -b 0.0.0.0 -p $PORT ITIHub.asgi:application
else
    echo "Starting Gunicorn server (WebSockets disabled)..."
    exec gunicorn ITIHub.wsgi:application --bind 0.0.0.0:$PORT --workers 4
fi
