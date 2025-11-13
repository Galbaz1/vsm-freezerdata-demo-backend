# Example Dockerfile for Railway Deployment
# This is a reference - rename to Dockerfile when ready to deploy

FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies (if needed for pandas/parquet)
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./
COPY MANIFEST.in ./
COPY README.md ./

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy application code
COPY elysia/ ./elysia/
COPY features/ ./features/

# Copy static files (frontend build + images)
COPY elysia/api/static/ ./elysia/api/static/

# Copy telemetry data (parquet file)
COPY features/telemetry/timeseries_freezerdata/ ./features/telemetry/timeseries_freezerdata/

# Copy config JSON files
COPY features/integration_vsm/output/ ./features/integration_vsm/output/

# Expose port (Railway sets $PORT automatically)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:${PORT:-8000}/api/health')" || exit 1

# Start command
# Railway provides $PORT environment variable
# Use --reload false for production
CMD elysia start --host 0.0.0.0 --port ${PORT:-8000} --reload false

