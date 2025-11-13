# Railway Deployment Research - VSM Freezer Demo Backend

**Date**: January 2025  
**Status**: Research Complete - Ready for Implementation

---

## Executive Summary

The VSM Freezer Demo backend can be deployed to Railway with minimal changes. **No Railway database is needed** - the app uses external Weaviate Cloud. Data files (~72MB total) can be bundled in the deployment or stored in Railway persistent volumes.

---

## Application Architecture

### Current Stack
- **Framework**: FastAPI (Elysia)
- **Python**: 3.12 (required)
- **Start Command**: `elysia start` → `uvicorn elysia.api.app:app --host 0.0.0.0 --port $PORT`
- **Port**: Railway provides `$PORT` environment variable

### External Dependencies
1. **Weaviate Cloud** (external, not Railway)
   - Connection via `WCD_URL` + `WCD_API_KEY` env vars
   - Already configured in `.env`
   - **No Railway database needed** ✅

2. **LLM APIs** (external)
   - Gemini API (`GEMINI_API_KEY`)
   - Other providers via OpenRouter (optional)
   - All via environment variables

---

## Data Dependencies Analysis

### File Inventory

| Type | Path | Size | Required? | Notes |
|------|------|------|-----------|-------|
| **Parquet** | `features/telemetry/timeseries_freezerdata/135_1570_cleaned_with_flags.parquet` | 8.9MB | ✅ Yes | Telemetry data (785K rows) |
| **Static Files** | `elysia/api/static/` | 63MB | ✅ Yes | Frontend build + 233 manual images + 8 diagrams |
| **JSON Config** | `features/integration_vsm/output/fd_assets_enrichment.json` | <1MB | ✅ Yes | Commissioning data (Context C) |
| **JSONL Data** | `features/manuals_vsm/output/*.jsonl` | <5MB | ❌ No | Already in Weaviate |
| **JSONL Data** | `features/vlogs_vsm/output/*.jsonl` | <1MB | ❌ No | Already in Weaviate |
| **Extraction Output** | `features/extraction/production_output/` | ~50MB | ❌ No | Source files, images already copied to static |

**Total Required**: ~73MB

### Data Access Patterns

1. **Parquet File** (`WorldStateEngine`)
   - Read-only access
   - Loaded on-demand (lazy loading)
   - Path: `features/telemetry/timeseries_freezerdata/135_1570_cleaned_with_flags.parquet`
   - Used by: `compute_worldstate`, `get_asset_health`, `visualize_temperature_timeline`

2. **Static Files** (`elysia/api/static/`)
   - Served via FastAPI `StaticFiles`
   - Includes:
     - Frontend build (`/_next`, `/static`)
     - Manual images (`/static/manual_images/`)
     - Diagrams (`/static/diagrams/`)

3. **JSON Config** (`fd_assets_enrichment.json`)
   - Read at startup/runtime
   - Used for Context C (commissioning data)

---

## Railway Deployment Options

### Option 1: Bundle Everything in Docker Image (Recommended)

**Pros**:
- Simple deployment (single service)
- No persistent volume management
- Fast cold starts
- Data always available

**Cons**:
- Larger image size (~73MB data)
- Image rebuild required for data updates

**Implementation**:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Copy requirements and install
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

# Copy application code
COPY elysia/ ./elysia/
COPY features/ ./features/

# Copy static files and data
COPY elysia/api/static/ ./elysia/api/static/
COPY features/telemetry/ ./features/telemetry/
COPY features/integration_vsm/output/ ./features/integration_vsm/output/

# Expose port (Railway sets $PORT)
EXPOSE 8000

# Start command
CMD ["elysia", "start", "--host", "0.0.0.0", "--port", "${PORT:-8000}", "--reload", "false"]
```

**Railway Config**:
- Service type: Docker
- Build: Dockerfile
- Environment variables: Copy from `.env` (Weaviate, Gemini keys)

---

### Option 2: Persistent Volume for Data

**Pros**:
- Smaller Docker image
- Data can be updated without rebuild
- Better for frequently changing data

**Cons**:
- More complex setup
- Volume management overhead
- Cost: $0.15/GB/month (~$0.01/month for 73MB)

**Implementation**:
1. Mount volume at `/app/data`
2. Copy data files to volume during first deploy
3. Update code paths to read from `/app/data`

**Railway Config**:
- Service type: Docker
- Persistent volume: `/app/data` (73MB)
- Mount data during build/deploy

---

### Option 3: External Storage (S3/GCS)

**Pros**:
- Smallest Docker image
- Scalable storage
- Can update data independently

**Cons**:
- Requires storage service setup
- Code changes needed (download on startup)
- Network latency for data access

**Not Recommended**: Overkill for 73MB of static data

---

## Railway Database Services

### Do We Need Railway Databases?

**Answer: NO** ✅

**Why**:
- App uses **Weaviate Cloud** (external service)
- No PostgreSQL/MySQL/Redis required
- All vector data in Weaviate
- No relational database needed

**Railway Database Options** (for reference):
- PostgreSQL: $0.15/GB/month + compute
- MySQL: $0.15/GB/month + compute  
- Redis: $0.15/GB/month + compute
- MongoDB: $0.15/GB/month + compute

**When Would We Need Railway DB?**
- If migrating from Weaviate Cloud to self-hosted Weaviate
- If adding user authentication/sessions (could use Redis)
- If adding application state storage (could use PostgreSQL)

**Current State**: External Weaviate Cloud is sufficient ✅

---

## Deployment Checklist

### Pre-Deployment

- [ ] Create `Dockerfile` (Option 1 recommended)
- [ ] Create `.dockerignore` (exclude `.venv`, `__pycache__`, `.git`)
- [ ] Test Docker build locally
- [ ] Verify all environment variables documented
- [ ] Check file paths are relative (not absolute)

### Railway Setup

- [ ] Create Railway project
- [ ] Connect GitHub repository (or deploy via CLI)
- [ ] Set environment variables:
  - `WCD_URL` (Weaviate Cloud URL)
  - `WCD_API_KEY` (Weaviate Cloud API key)
  - `GEMINI_API_KEY` (Gemini API key)
  - `BASE_MODEL=gemini-2.5-flash`
  - `COMPLEX_MODEL=gemini-2.5-pro`
  - `BASE_PROVIDER=gemini`
  - `COMPLEX_PROVIDER=gemini`
  - `WEAVIATE_IS_LOCAL=False`
- [ ] Configure service:
  - Build: Dockerfile
  - Port: Auto-detected from `$PORT`
  - Start command: Auto (from Dockerfile CMD)

### Post-Deployment

- [ ] Verify health endpoint: `https://your-app.railway.app/api/health`
- [ ] Test Weaviate connection
- [ ] Test static file serving (`/static/manual_images/`)
- [ ] Test parquet data access (via `compute_worldstate` tool)
- [ ] Monitor logs for errors
- [ ] Set up custom domain (optional)

---

## Environment Variables Reference

### Required

```bash
# Weaviate Cloud
WCD_URL=https://your-cluster.weaviate.cloud
WCD_API_KEY=your-api-key
WEAVIATE_IS_LOCAL=False

# Gemini API
GEMINI_API_KEY=your-gemini-key
BASE_MODEL=gemini-2.5-flash
COMPLEX_MODEL=gemini-2.5-pro
BASE_PROVIDER=gemini
COMPLEX_PROVIDER=gemini
```

### Optional

```bash
# Logging
LOGGING_LEVEL=INFO

# Model API Base (if using custom endpoint)
MODEL_API_BASE=

# OpenRouter (if using)
OPENROUTER_API_KEY=
```

---

## Code Changes Required

### Minimal Changes Needed

1. **Port Configuration** (`elysia/api/cli.py`)
   - Already supports `--port` flag ✅
   - Railway provides `$PORT` env var
   - Update CMD to use `$PORT` or default to 8000

2. **File Paths** (verify relative paths)
   - ✅ Parquet: `features/telemetry/...` (relative)
   - ✅ Static: `elysia/api/static/` (relative)
   - ✅ JSON: `features/integration_vsm/output/...` (relative)

3. **Host Binding**
   - ✅ Already uses `0.0.0.0` in Dockerfile CMD
   - ✅ FastAPI serves on all interfaces

### No Changes Needed

- ✅ Weaviate connection (uses env vars)
- ✅ Static file serving (FastAPI StaticFiles)
- ✅ Logging (writes to files, Railway captures stdout)
- ✅ Frontend serving (already configured)

---

## Railway Pricing Estimate

### Service Costs

| Resource | Usage | Cost |
|----------|-------|------|
| **Base Plan** | Hobby ($5/mo) or Pro ($20/mo) | $5-20/mo |
| **CPU** | 0.5 vCPU (idle most of time) | ~$10/mo |
| **Memory** | 1GB RAM | $10/mo |
| **Network** | <10GB egress/month | <$1/mo |
| **Persistent Volume** | 0GB (bundled in image) | $0/mo |

**Estimated Total**: $15-30/month (Hobby plan)

### Cost Optimization

- Use Hobby plan ($5/mo) for development
- Scale down when idle (Railway auto-scales)
- Monitor usage in Railway dashboard

---

## Railway vs Alternatives

### Why Railway?

✅ **Pros**:
- Simple Docker deployment
- Automatic HTTPS
- Environment variable management
- Built-in logging
- Usage-based pricing (pay for actual usage)
- Good for Python/FastAPI apps

❌ **Cons**:
- No built-in Weaviate (but we use external cloud)
- Persistent volumes cost extra (but we bundle data)
- Less control than VPS

### Alternatives Considered

1. **Render**: Similar to Railway, but Railway has better Python support
2. **Fly.io**: More complex, better for global distribution
3. **Heroku**: More expensive, similar simplicity
4. **AWS/GCP**: More complex, better for scale

**Verdict**: Railway is ideal for this use case ✅

---

## Next Steps

1. **Create Dockerfile** (Option 1 - bundle everything)
2. **Test locally**: `docker build -t vsm-backend . && docker run -p 8000:8000 vsm-backend`
3. **Deploy to Railway**: `railway up` or connect GitHub repo
4. **Set environment variables** in Railway dashboard
5. **Verify deployment** via health check endpoint
6. **Test full workflow** (query → Weaviate → parquet → response)

---

## References

- [Railway FastAPI Guide](https://docs.railway.com/guides/fastapi)
- [Railway Docker Deployment](https://docs.railway.com/guides/docker)
- [Railway Environment Variables](https://docs.railway.com/guides/environment-variables)
- [Railway Persistent Volumes](https://docs.railway.com/guides/persistent-volumes)
- [Railway Pricing](https://railway.com/pricing)

---

## Questions Answered

### ✅ Do we need Railway databases?
**No** - We use external Weaviate Cloud. Railway databases (PostgreSQL, MySQL, Redis) are not needed.

### ✅ How do we handle local data files?
**Bundle in Docker image** (Option 1) - simplest approach for 73MB of mostly static data.

### ✅ Can Railway serve static files?
**Yes** - FastAPI `StaticFiles` works perfectly. Files are served from `elysia/api/static/`.

### ✅ How do we connect to Weaviate?
**Environment variables** - `WCD_URL` and `WCD_API_KEY` configured in Railway dashboard.

### ✅ What about the parquet file?
**Include in Docker image** - 8.9MB file bundled with code. Read-only access, no updates needed.

---

**Research Status**: ✅ Complete  
**Recommendation**: Deploy using Option 1 (Docker bundle)  
**Complexity**: Low (minimal code changes)  
**Estimated Setup Time**: 30-60 minutes

