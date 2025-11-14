# Railway Deployment Issues - Root Cause Analysis

**Date**: November 13, 2025  
**Status**: Diagnosed - Ready to Fix

---

## Issues Identified from User Screenshots

### ✅ WORKING
1. **Diagram tool** - Shows SMIDO overview PNG correctly
2. **Query tool** - Finds VSM_WorldStateSnapshot data  
3. **search_manual_images** - Finds 2 images from Weaviate
4. **VSM config** - Dutch prompts, correct agent persona loaded
5. **Bootstrap** - vsm_smido bootstrapper registered and applied

### ❌ NOT WORKING
1. **Manual images display** - Shows URL text instead of actual images
2. **Visualization tool** - Crashes with pyarrow/fastparquet import errors

---

## Root Cause #1: Hardcoded localhost URLs in Weaviate

### The Problem

Image URLs stored in Weaviate:
```
http://localhost:8000/static/manual_images/opbouw-werking/chunk-{id}.png
```

**Railway domain**:
```
https://hva-elysia.up.railway.app
```

**Result**: Frontend tries to load `http://localhost:8000/...` which doesn't exist on Railway!

### Evidence

**File**: `scripts/upload_manual_images_weaviate.py` line 109
```python
image_url = f"http://localhost:8000/static/manual_images/{img['manual_name']}/{filename}"
```

**Weaviate Data** (from screenshots):
- Images found: 2 results
- But frontend can't load them (wrong domain)

### Why This Happens

The upload script ran **locally**, so URLs were generated as `localhost:8000`. When the app runs on Railway, those URLs are invalid.

---

## Root Cause #2: Missing Parquet Dependencies

### The Problem

Pandas needs `pyarrow` or `fastparquet` to read `.parquet` files.

**Error from screenshot**:
```
Error computing WorldState: Unable to find a usable engine;
tried using: 'pyarrow', 'fastparquet'. A suitable version of
pyarrow or fastparquet is required for parquet support.
```

### Evidence

**File**: `pyproject.toml` line 41
```python
dependencies = [
    ...
    "pandas>=2.0.0",  # ← Added, but NO pyarrow!
]
```

**Parquet file location**:
```
features/telemetry/timeseries_freezerdata/135_1570_cleaned_with_flags.parquet
```

**Used by**:
- `compute_worldstate` (line 793 in custom_tools.py)
- `get_asset_health` (line 915)
- `analyze_sensor_pattern` (line 1111)
- `visualize_temperature_timeline` (line 1464)

---

## Complete Fix Plan

### Fix 1: Dynamic Image URLs (CRITICAL)

**Problem**: Hardcoded localhost URLs in Weaviate  
**Solution**: Make URLs relative or use environment variable

#### Option A: Relative URLs (Recommended)

**Change upload script**:
```python
# Instead of:
image_url = f"http://localhost:8000/static/manual_images/..."

# Use:
image_url = f"/static/manual_images/{img['manual_name']}/{filename}"
```

**Benefits**:
- Works on any domain (localhost, Railway, custom)
- Frontend resolves to current host automatically
- No environment variables needed

**Action Required**:
1. Update `scripts/upload_manual_images_weaviate.py` line 109
2. Re-run script locally to update Weaviate
3. Verify images load on Railway

#### Option B: Environment Variable

**Add to Railway env vars**:
```bash
PUBLIC_URL=https://hva-elysia.up.railway.app
```

**Change upload script**:
```python
base_url = os.getenv("PUBLIC_URL", "http://localhost:8000")
image_url = f"{base_url}/static/manual_images/..."
```

**Action Required**:
1. Update upload script to use env var
2. Add PUBLIC_URL to Railway
3. Re-run script on Railway (via railway run)

#### Recommendation: **Option A** (relative URLs)
- Simpler
- No env var management
- Works everywhere

---

### Fix 2: Add Parquet Dependencies

**Problem**: pandas can't read parquet files  
**Solution**: Add pyarrow to dependencies

**File**: `pyproject.toml`
```python
dependencies = [
    ...
    "pandas>=2.0.0",
    "pyarrow>=14.0.0",  # ← ADD THIS
]
```

**Why pyarrow over fastparquet?**
- Faster
- Better maintained
- Recommended by pandas docs
- Smaller install size

**Action Required**:
1. Add `"pyarrow>=14.0.0"` to pyproject.toml
2. Git commit + push → Railway rebuilds automatically
3. Test visualization tools

---

### Fix 3: Verify Static File Serving (Investigation)

**Current setup** (`elysia/api/app.py` lines 107-114):
```python
app.mount("/_next", StaticFiles(directory=BASE_DIR / "static/_next"))
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"))
```

**Should work for**:
- `/static/manual_images/` ✅
- `/static/diagrams/` ✅

**Test on Railway**:
```bash
curl https://hva-elysia.up.railway.app/static/diagrams/smido_overview.png
```

**Expected**: Image bytes  
**If fails**: Check if files were copied to Docker image

---

## Implementation Sequence

### Phase 1: Fix Parquet Dependencies (5 min)
1. Add `pyarrow>=14.0.0` to pyproject.toml
2. Commit + push → auto-deploy
3. Test: "Visualiseer de temperatuur van de laatste 24 uur"

### Phase 2: Fix Image URLs (10 min)
1. Update `scripts/upload_manual_images_weaviate.py`:
   - Change line 109 to use relative URLs
2. Run locally: `source .venv/bin/activate && python3 scripts/upload_manual_images_weaviate.py`
3. Verify: All 233 images re-uploaded with `/static/...` URLs
4. Test on Railway: "Laat me een foto zien van een verdamper"

### Phase 3: Verification (5 min)
1. Test all VSM tools:
   - ✅ compute_worldstate (needs pyarrow)
   - ✅ search_manual_images (needs relative URLs)
   - ✅ visualize_temperature_timeline (needs both)
2. Test static file serving:
   - `curl https://hva-elysia.up.railway.app/static/diagrams/smido_overview.png`
   - `curl https://hva-elysia.up.railway.app/static/manual_images/opbouw-werking/chunk-{some-id}.png`

---

## Why Railway Database is NOT Needed

### Current Setup ✅
- **Weaviate**: External cloud (mrslrqo5rzkqafoqgbvdw.c0.europe-west3.gcp.weaviate.cloud)
- **Static files**: Bundled in Docker image (63MB in elysia/api/static/)
- **Parquet data**: Bundled in Docker image (8.9MB)

### Why No Database Needed
- Images are **static files** served by FastAPI (not database BLOBs)
- Parquet file is **read-only** (no writes needed)
- All metadata in Weaviate (external)

### When You WOULD Need Railway Database
- If you wanted to store images as BLOBs (not recommended - static files are better)
- If you needed user-generated content storage
- If you wanted to replace Weaviate with self-hosted PostgreSQL+pgvector (not recommended)

**Verdict**: Static file serving via FastAPI is the correct approach ✅

---

## Technical Details

### Static File Serving on Railway

**How it works**:
1. Files copied to Docker image: `COPY elysia/api/static/ ./elysia/api/static/`
2. FastAPI mounts directory: `app.mount("/static", StaticFiles(...))`
3. Railway serves on port $PORT (auto-detected)
4. Public URL: `https://hva-elysia.up.railway.app/static/...`

**Verification**:
```bash
# Test if file exists in Docker image
railway run ls -la elysia/api/static/manual_images/opbouw-werking/ | head

# Test if FastAPI serves it
curl -I https://hva-elysia.up.railway.app/static/diagrams/smido_overview.png
```

---

## Summary

### Issues
1. ❌ **Image URLs**: Hardcoded `localhost:8000` in Weaviate (233 images)
2. ❌ **Visualization**: Missing `pyarrow` dependency for parquet files

### Fixes
1. ✅ **Quick win**: Add `pyarrow>=14.0.0` to pyproject.toml (5 min)
2. ✅ **Complete fix**: Update image URLs to relative paths + re-upload (10 min)

### No Railway Database Needed
- ✅ Static files served via FastAPI
- ✅ Images bundled in Docker image
- ✅ Weaviate external (cloud)

**Total fix time**: ~20 minutes  
**Complexity**: Low


