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

# Copy application code (needed for editable install)
COPY elysia/ ./elysia/

# Install Python dependencies (after copying code for editable install)
RUN pip install --no-cache-dir -e .

# Copy startup scripts (needed for auto-seed)
COPY scripts/auto_seed_on_startup.py ./scripts/
COPY scripts/seed_default_config.py ./scripts/

# Copy ONLY required feature data (explicitly to avoid .dockerignore conflicts)
# Create directories first, then copy files
RUN mkdir -p ./features/telemetry/timeseries_freezerdata/ \
    ./features/integration_vsm/output/ \
    ./features/telemetry_vsm/ \
    ./features/vsm_tree/

# Telemetry data (parquet files - 9MB) - copy individually to ensure they're included
COPY features/telemetry/timeseries_freezerdata/135_1570_cleaned_with_flags.parquet ./features/telemetry/timeseries_freezerdata/

# Integration data (commissioning JSON)
COPY features/integration_vsm/output/fd_assets_enrichment.json ./features/integration_vsm/output/

# Telemetry VSM (WorldState engine - Python files)
COPY features/telemetry_vsm/*.py ./features/telemetry_vsm/

# VSM tree (bootstrap, context manager, orchestrator - Python files)
COPY features/vsm_tree/*.py ./features/vsm_tree/

# Static files (frontend build + images - 63MB)
COPY elysia/api/static/ ./elysia/api/static/

# Expose port (Railway sets $PORT automatically)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:${PORT:-8000}/api/health')" || exit 1

# Start command with auto-seed
# Railway provides $PORT environment variable
# Use --reload false for production
CMD python3 scripts/auto_seed_on_startup.py && elysia start --host 0.0.0.0 --port ${PORT:-8000} --reload false

