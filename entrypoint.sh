#!/bin/bash

set -e

echo "Starting entrypoint script..."

# Print environment variables for debugging
echo "Environment variables:"
echo "- SECRET_KEY: ${SECRET_KEY:0:3}..."
echo "- DEBUG: $DEBUG"
echo "- Current working directory: $(pwd)"

# Ensure ITIHub directory exists
mkdir -p /app/ITIHub

# Database URL handling - check in multiple locations
if [ -z "$DATABASE_URL" ]; then
    echo "DATABASE_URL not set in environment, checking other sources..."
    
    # Try to get from .env file in app root
    if [ -f "/app/.env" ]; then
        echo "Checking /app/.env file..."
        db_url_app=$(grep -E '^DATABASE_URL=' /app/.env | cut -d '=' -f2- | tr -d '"' | tr -d "'" | sed 's/^[ \t]*//;s/[ \t]*$//')
        if [ -n "$db_url_app" ]; then
            echo "Found DATABASE_URL in /app/.env"
            export DATABASE_URL="$db_url_app"
        fi
    fi
    
    # If still not set, try ITIHub/.env
    if [ -z "$DATABASE_URL" ] && [ -f "/app/ITIHub/.env" ]; then
        echo "Checking /app/ITIHub/.env file..."
        db_url_itihub=$(grep -E '^DATABASE_URL=' /app/ITIHub/.env | cut -d '=' -f2- | tr -d '"' | tr -d "'" | sed 's/^[ \t]*//;s/[ \t]*$//')
        if [ -n "$db_url_itihub" ]; then
            echo "Found DATABASE_URL in /app/ITIHub/.env"
            export DATABASE_URL="$db_url_itihub"
        fi
    fi
fi

# If DATABASE_URL is still not set after checking all sources
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL is still not set! Using fallback Neon DB URL"
    export DATABASE_URL="postgresql://neondb_owner:npg_Imx5LjVO2evH@ep-ancient-snow-a402yv88-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require"
fi

echo "DATABASE_URL is now: ${DATABASE_URL:0:30}..."

# Copy or create .env file with the DATABASE_URL included
echo "Creating or updating .env file in ITIHub directory"
cat > /app/ITIHub/.env << EOF
# Generated .env file
DATABASE_URL=${DATABASE_URL}
SECRET_KEY=${SECRET_KEY:-"django-insecure-default-key"}
DEBUG=${DEBUG:-False}
ALLOWED_HOSTS=${ALLOWED_HOSTS:-"localhost,127.0.0.1,.up.railway.app,.neon.tech"}
CORS_ALLOW_ALL_ORIGINS=${CORS_ALLOW_ALL_ORIGINS:-True}
ENABLE_WEBSOCKET=${ENABLE_WEBSOCKET:-true}
EOF

# Navigate to the directory containing manage.py
echo "Current directory before cd: $(pwd)"
cd /app/ITIHub
echo "Changed to directory: $(pwd)"
echo "Listing directory contents:"
ls -la

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
    print('DATABASE_URL not set, cannot continue')
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

# Determine port for server - Default to 8080 for Railway
PORT=${PORT:-8080}
echo "Starting server on port $PORT..."

# Add a health check endpoint for Railway
echo "Creating health check endpoint..."
mkdir -p /app/ITIHub/ITIHub/
cat > /app/ITIHub/ITIHub/health_check.py << 'EOF'
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({"status": "healthy"})
EOF

# Check if we should run with WebSocket support
if [ "${ENABLE_WEBSOCKET:-true}" = "true" ]; then
    echo "Starting Daphne server with WebSocket support on port $PORT..."
    exec daphne -b 0.0.0.0 -p $PORT ITIHub.asgi:application
else
    echo "Starting Gunicorn server (WebSockets disabled) on port $PORT..."
    exec gunicorn ITIHub.wsgi:application --bind 0.0.0.0:$PORT --workers 4
fi
