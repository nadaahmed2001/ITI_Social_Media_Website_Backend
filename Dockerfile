FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV SECRET_KEY="django-insecure-default-key-for-dev-only-change-in-production"

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /ITIHub/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY . /app/

# Make the entry point script executable
RUN chmod +x /app/ITIHub/entrypoint.sh

# Expose the port
EXPOSE $PORT

# Run the application
ENTRYPOINT ["/app/ITIHub/entrypoint.sh"]
