#!/bin/bash

# Navigate to the ITIHub directory where manage.py is located
cd /app/ITIHub

# Collect static files
python manage.py collectstatic --noinput

# Apply database migrations
python manage.py migrate

# Start server
gunicorn ITIHub.wsgi:application --bind 0.0.0.0:$PORT
