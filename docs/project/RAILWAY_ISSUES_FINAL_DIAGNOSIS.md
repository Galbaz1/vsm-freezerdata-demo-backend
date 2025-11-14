# Railway Deployment - Complete Issue Diagnosis & Fix Plan

**Date**: November 13, 2025  
**Status**: Multiple Issues Identified - Prioritized Fix Plan

---

## Current State

### ✅ WORKING
- App starts successfully on Railway
- Health endpoint responds: `{"status":"healthy"}`
- VSM config auto-seeds on startup
- `feature_bootstrappers: ["vsm_smido"]` correctly set
- OpenAI API keys added (both `OPENAI_API_KEY` and `OPENAI_APIKEY`)
- Trees can be created: `Successfully inserted new tree`
- No more "No tools available" crash on fresh conversations

### ❌ CRITICAL ISSUES

#### Issue #1: Port Number Type Error
**Error**: `ValueError: invalid literal for int() with base 10: '8080.0'`

**Location**: `elysia/api/utils/config.py:144` in `FrontendConfig.__init__`

**Cause**: 
```python
self.save_location_local_weaviate_port = int(os.getenv("LOCAL_WEAVIATE_PORT", 8080))
```
When loaded from Weaviate, ports are stored as floats (8080.0), causing int() to fail.

**Impact**: **Initialize_user crashes** for new users

**Fix**: Handle float-to-int conversion
```python
port_value = os.getenv("LOCAL_WEAVIATE_PORT", 8080)
self.save_location_local_weaviate_port = int(float(port_value)) if isinstance(port_value, str) else int(port_value)
```

**Priority**: 🔴 CRITICAL (blocks all new users)

---

#### Issue #2: Parquet Files Missing from Container
**Error**: `FileNotFoundError: /app/features/telemetry/timeseries_freezerdata/135_1570_cleaned_with_flags.parquet`

**Verification**:
```bash
railway run ls /app/features/
# Result: No such file or directory
```

**Cause**: `.dockerignore` or Dockerfile COPY not working correctly

**Impact**: **All WorldState tools crash**:
- `compute_worldstate`
- `get_asset_health`  
- `analyze_sensor_pattern`
- `visualize_temperature_timeline`

**Current Dockerfile** (lines 31-46):
```dockerfile
RUN mkdir -p ./features/telemetry/timeseries_freezerdata/ ...
COPY features/telemetry/timeseries_freezerdata/135_1570_cleaned_with_flags.parquet ...
COPY features/integration_vsm/output/fd_assets_enrichment.json ...
COPY features/telemetry_vsm/*.py ...
COPY features/vsm_tree/*.py ...
```

**Problem**: Wildcard `*.py` doesn't copy `__init__.py` files or subdirectories

**Fix**: Copy directories, not individual files
```dockerfile
COPY features/telemetry/ ./features/telemetry/
COPY features/integration_vsm/ ./features/integration_vsm/
COPY features/telemetry_vsm/ ./features/telemetry_vsm/
COPY features/vsm_tree/ ./features/vsm_tree/
```

**Priority**: 🔴 CRITICAL (breaks parquet-based tools)

---

#### Issue #3: Static Files (Manual Images) Missing
**Error**: `ls: /app/elysia/api/static/manual_images/: No such file or directory`

**Verification**:
```bash
curl https://hva-elysia.up.railway.app/static/manual_images/opbouw-werking/chunk-xxx.png
# Result: 404
```

**Cause**: `COPY elysia/api/static/` might be excluding subdirectories due to `.dockerignore`

**Impact**: **Manual images don't display** (only show URL text)

**Current Dockerfile** (line 49):
```dockerfile
COPY elysia/api/static/ ./elysia/api/static/
```

**Possible issue**: 
- `.dockerignore` blocking `elysia/` subdirectories?
- Static files copied BEFORE being populated?

**Fix**: Verify `.dockerignore` doesn't block elysia/api/static/

**Priority**: 🟡 HIGH (visual content broken)

---

#### Issue #4: Saved Trees Loading Without Tools
**Warning**: `In saved tree, custom tool 'get_current_status' found. This will not be loaded in the new tree.`

**Cause**: Old trees saved to `ELYSIA_TREES__` before bootstrap system, trying to reload

**Impact**: Loading old conversations fails gracefully (warning, not error)

**Fix**: Clear `ELYSIA_TREES__` collection (already done locally)

**Priority**: 🟢 LOW (cosmetic warnings, doesn't break functionality)

---

## Root Cause Analysis

### Why Files Are Missing

**Theory**: `.dockerignore` is being ignored or misapplied

**Evidence**:
1. Build logs show COPY commands execute ✅
2. But files don't exist in running container ❌
3. `railway run` can't find `/app` directory

**Hypothesis**: Railway is using Nixpacks instead of Dockerfile for some deployments

**Proof Needed**: Check deployment metadata

From latest deployment:
```json
"serviceManifest": {
  "build": {
    "builder": "DOCKERFILE",  ← Should use Dockerfile
    "dockerfilePath": "Dockerfile"
  }
}
```

**Confirmed**: Using Dockerfile ✅

**Alternative hypothesis**: COPY commands complete but files end up in wrong layer/stage

---

## Complete Fix Plan (Prioritized)

### Fix 1: Port Number Type Conversion (CRITICAL - 5 min)

**File**: `elysia/api/utils/config.py` lines 144-149

**Current**:
```python
self.save_location_local_weaviate_port = int(os.getenv("LOCAL_WEAVIATE_PORT", 8080))
self.save_location_local_weaviate_grpc_port = int(os.getenv("LOCAL_WEAVIATE_GRPC_PORT", 50051))
```

**Fix**:
```python
def safe_int_port(value, default):
    """Convert port value to int, handling float strings from Weaviate."""
    if isinstance(value, str):
        return int(float(value))  # Handle "8080.0" strings
    return int(value) if value else default

self.save_location_local_weaviate_port = safe_int_port(
    os.getenv("LOCAL_WEAVIATE_PORT", 8080), 8080
)
self.save_location_local_weaviate_grpc_port = safe_int_port(
    os.getenv("LOCAL_WEAVIATE_GRPC_PORT", 50051), 50051
)
```

Apply to ALL 4 port fields (LOCAL + CUSTOM)

**Test**: `curl -X POST https://hva-elysia.up.railway.app/init/user/test-$(date +%s)`

---

### Fix 2: Simplify Dockerfile - Copy Whole Directories (CRITICAL - 10 min)

**File**: `Dockerfile`

**Problem**: Current approach with mkdir + individual files is fragile

**Solution**: Trust `.dockerignore` and copy directories simply

**New Dockerfile** (lines 25-43):
```dockerfile
# Copy startup scripts
COPY scripts/auto_seed_on_startup.py ./scripts/
COPY scripts/seed_default_config.py ./scripts/

# Copy ALL features (let .dockerignore handle exclusions)
COPY features/ ./features/

# Copy static files  
COPY elysia/api/static/ ./elysia/api/static/
```

**Update .dockerignore** to be explicit:
```dockerfile
# Exclude specific large directories
features/extraction/
features/manuals_vsm/output/
features/vlogs_vsm/output/
features/diagrams_vsm/src/
features/diagrams_vsm/output/

# Everything else in features/ will be included:
# - features/telemetry/ ✅
# - features/integration_vsm/ ✅
# - features/telemetry_vsm/ ✅
# - features/vsm_tree/ ✅
```

**Test**: 
```bash
railway run ls -lh /app/features/telemetry/timeseries_freezerdata/
# Expected: 135_1570_cleaned_with_flags.parquet (8.9M)
```

---

### Fix 3: Verify Static Files Copy (HIGH - 5 min)

**Investigation needed**:
```bash
# Check if static files are in Docker image
railway run ls -la /app/elysia/api/static/
railway run ls -la /app/elysia/api/static/manual_images/opbouw-werking/ | head
```

**If missing**: 
- Check if `elysia/api/static/` was excluded by `.dockerignore`
- Ensure COPY happens AFTER pip install (currently line 49)

**If exists but 404**:
- Check FastAPI StaticFiles mount path
- Verify `BASE_DIR` resolves correctly in production

---

### Fix 4: Clear Old Saved Trees (LOW - Already Done Locally)

**Action**: Run on Railway to clear production Weaviate
```bash
railway run python3 <<EOF
import asyncio
from elysia.util.client import ClientManager

async def clear():
    cm = ClientManager()
    async with cm.connect_to_async_client() as client:
        if await client.collections.exists("ELYSIA_TREES__"):
            await client.collections.delete("ELYSIA_TREES__")
            print("✅ Deleted")
    await cm.close_clients()

asyncio.run(clear())
EOF
```

---

## Implementation Sequence

### Phase 1: Critical Fixes (15 min)

1. **Fix port conversion** in `config.py` (5 min)
2. **Simplify Dockerfile** to `COPY features/ ./features/` (5 min)  
3. **Verify .dockerignore** excludes only large dirs (5 min)
4. Commit + push → Railway auto-deploys

### Phase 2: Verification (10 min)

Test on **https://hva-elysia.up.railway.app**:

```bash
# 1. Check files exist
railway run ls -lh /app/features/telemetry/timeseries_freezerdata/
railway run ls -lh /app/elysia/api/static/manual_images/opbouw-werking/ | head

# 2. Test parquet tools
# Query: "Bereken de WorldState van de laatste 24 uur"
# Expected: WorldState computed ✅ (not FileNotFoundError)

# 3. Test images
# Query: "Laat me een foto van een verdamper zien"  
# Expected: Images display ✅ (not just URL text)

# 4. Test Weaviate query
# Query: "Zoek informatie over deurgebruik"
# Expected: Results ✅ (not OpenAI API key error)
```

### Phase 3: Clean Up (5 min)

```bash
# Delete old trees from Weaviate
railway run python3 -c "import asyncio; from elysia.util.client import ClientManager; ..."
```

---

## Expected Results After Fixes

### User Experience (Any Browser):
1. Open https://hva-elysia.up.railway.app
2. Fresh localStorage → new user_id generated
3. Backend loads VSM config from Weaviate (`default_user` fallback) ✅
4. All 16 tools available ✅
5. Queries work:
   - Manual search ✅
   - Image search ✅ (with actual images, not URLs)
   - WorldState computation ✅ (parquet data accessible)
   - Visualizations ✅ (pandas + pyarrow working)
6. Dutch prompts, friendly VSM tone ✅

### Technical Verification:
- `/app/features/telemetry/` exists with parquet files
- `/app/elysia/api/static/manual_images/` exists with 233 PNGs
- Port conversion doesn't crash
- No FileNotFoundError in logs
- No "No tools available" errors

---

## Summary

### Critical Issues (Must Fix):
1. 🔴 **Port type conversion** → crashes initialize_user
2. 🔴 **Parquet files missing** → crashes WorldState tools
3. 🟡 **Images missing** → visual content broken

### Root Cause:
Dockerfile COPY strategy too granular with wildcards → files not copied correctly

### Solution:
- Simple `COPY features/ ./features/` 
- Let `.dockerignore` handle exclusions
- Fix port type conversion in config.py

### Time Estimate:
- Fixes: 15 minutes
- Deploy + test: 10 minutes
- **Total**: 25 minutes to full working state

