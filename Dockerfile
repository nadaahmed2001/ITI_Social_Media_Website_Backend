FROM python:3.10-slim-bookworm

# Upgrade system packages to reduce vulnerabilities
RUN apt-get update && apt-get upgrade -y && apt-get clean

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Install additional WebSocket dependencies
RUN pip install daphne channels channels_redis

# Copy project
COPY . /app/

# Make sure the ITIHub directory exists
RUN mkdir -p /app/ITIHub


# Create health check endpoint
RUN echo 'from django.http import JsonResponse\n\ndef health_check(request):\n    return JsonResponse({"status": "healthy"})' > /app/ITIHub/health_check.py

# Expose the port
EXPOSE 8000

# Run the application
ENTRYPOINT ["daphne", "-b", "0.0.0.0", "-p", "8000", "ITIHub.asgi:application"]
