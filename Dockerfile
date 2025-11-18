# Root Dockerfile for Render - Backend Service
# This file is used when Render doesn't detect render.yaml or for manual service creation
# For Blueprint deployment, use render.yaml instead

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY backend/requirements.txt ./requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY backend/ ./backend/
COPY opus/ ./opus/

# Set working directory to backend for imports
WORKDIR /app/backend

# Create uploads directory
RUN mkdir -p uploads/images uploads/documents

# Set Python path to include backend
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/')" || exit 1

# Run the application (production mode - no reload)
# Render will set PORT environment variable, but we default to 8000
# Using shell form to support environment variable substitution
# Working directory is already set to /app/backend
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]

