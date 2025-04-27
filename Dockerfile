FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV SECRET_KEY="django-insecure-default-key-for-dev-only-change-in-production"
ENV ENABLE_WEBSOCKET=true

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Install additional WebSocket dependencies
RUN pip install daphne channels channels_redis

# Copy project
COPY . /app/

# Make the entry point script executable
RUN chmod +x entrypoint.sh

# Expose the port
EXPOSE $PORT

# Run the application
ENTRYPOINT ["./entrypoint.sh"]
