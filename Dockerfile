FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV SECRET_KEY="django-insecure-default-key-for-dev-only-change-in-production"
ENV ENABLE_WEBSOCKET=true

# Default DATABASE_URL - will be overridden by environment variables if provided
ENV DATABASE_URL="postgresql://neondb_owner:npg_Imx5LjVO2evH@ep-ancient-snow-a402yv88-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require"

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Install additional WebSocket dependencies
RUN pip install daphne channels channels_redis

# Create .env file with DATABASE_URL
RUN echo "DATABASE_URL=${DATABASE_URL}" > /app/.env && \
    echo "SECRET_KEY=${SECRET_KEY}" >> /app/.env && \
    echo "DEBUG=False" >> /app/.env && \
    echo "ALLOWED_HOSTS=localhost,127.0.0.1,.up.railway.app,.neon.tech" >> /app/.env && \
    echo "ENABLE_WEBSOCKET=true" >> /app/.env

# Copy project
COPY . /app/

# Make sure the ITIHub directory exists
RUN mkdir -p /app/ITIHub

# Copy the .env file to the ITIHub directory
RUN cp /app/.env /app/ITIHub/.env

# Make the entry point script executable
RUN chmod +x entrypoint.sh

# Create health check endpoint
RUN mkdir -p /app/ITIHub/ITIHub/
RUN echo 'from django.http import JsonResponse\n\ndef health_check(request):\n    return JsonResponse({"status": "healthy"})' > /app/ITIHub/ITIHub/health_check.py

# Expose the port
EXPOSE $PORT

# Run the application
ENTRYPOINT ["./entrypoint.sh"]
