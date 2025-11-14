# Railway Cross-Browser Issue - Deep Dive Analysis

**Date**: November 13, 2025  
**Issue**: App works in Chrome (Mac) but not Safari or other devices on Railway

---

## Symptom Analysis

### Works (Chrome on Mac):
- ✅ VSM config loads
- ✅ Tools available
- ✅ History persists
- ✅ Settings persist

### Doesn't Work (Safari / Other Devices):
- ❌ Generic Elysia config loads (not VSM)
- ❌ No tools available / wrong tools
- ❌ No history
- ❌ Settings reset

**User Statement**: "waarom afhankelijk van chrome cache terwijl we op railway published zijn?"

---

## Root Cause Hypothesis

This is **NOT** a browser cache issue. This is a **localStorage + server-side state mismatch**.

### How Elysia User State Works

#### Frontend (Browser):
1. On first visit: Generate random `user_id` (via `getDeviceId()` likely)
2. Store `user_id` in **localStorage** (browser-specific)
3. Use this `user_id` for ALL API calls: `/init/user/{user_id}`

#### Backend (Railway):
1. Receives `/init/user/{user_id}` request
2. Checks Weaviate for config with matching `user_id`
3. If found → load VSM config
4. If NOT found → create default Elysia config

### The Problem Chain

**Chrome on Mac** (Works):
1. localStorage has `user_id = "abc123"` (from previous local dev)
2. Sends: `POST /init/user/abc123`
3. Backend checks Weaviate for `user_id="abc123"` config
4. **IF** you ran `seed_default_config.py` with this user_id → VSM config found ✅
5. **OR** fallback to `default_user` config works → VSM config found ✅

**Safari / Other Device** (Fails):
1. localStorage is empty (new browser/device)
2. Generates NEW `user_id = "xyz789"`
3. Sends: `POST /init/user/xyz789`
4. Backend checks Weaviate for `user_id="xyz789"` config
5. **NOT FOUND** → checks `default_user` fallback
6. **IF** `default_user` config exists → VSM config loads ✅
7. **IF NOT** → creates generic Elysia config ❌

---

## Current Config State in Weaviate

From seed logs:
```
✅ Updated existing config: VSM Default Config
   User ID: default_user
   Default: True
   Feature Bootstrappers: vsm_smido
```

**Config exists with**:
- `user_id = "default_user"`
- `default = True`

**Fallback logic** (elysia/api/routes/init.py lines 37-46):
```python
# Fallback to global default_user config if user-specific not found
if len(default_configs.objects) == 0:
    default_configs = await collection.query.fetch_objects(
        filters=Filter.all_of([
            Filter.by_property("default").equal(True),
            Filter.by_property("user_id").equal("default_user"),
        ])
    )
```

**This SHOULD work** for any new user_id! 🤔

---

## Verification Needed

### Test 1: Check Default Config in Weaviate

Query Weaviate directly:
```python
filters=Filter.all_of([
    Filter.by_property("default").equal(True),
    Filter.by_property("user_id").equal("default_user"),
])
```

**Expected**: 1 config with `feature_bootstrappers: ["vsm_smido"]`  
**If fails**: Config not in Weaviate or encryption issue

### Test 2: Check Railway Environment

**Issue**: Railway containers are **stateless**
- No persistent filesystem (except volumes)
- `elysia/api/user_configs/` directory exists in Docker but is EMPTY
- Each container restart = fresh state

**User configs stored**:
- In-memory: `UserManager.users[user_id]` dict (lost on restart)
- On disk: `elysia/api/user_configs/frontend_config_{user_id}.json` (lost on Railway)
- In Weaviate: ELYSIA_CONFIG__ collection (persistent) ✅

### Test 3: CORS / Session Issues

Check if Safari blocks third-party cookies or localStorage access.

**Railway domain**: `https://hva-elysia.up.railway.app`  
**Potential issues**:
- Mixed content (HTTP in HTTPS)
- Cross-origin restrictions
- localStorage disabled in Safari private mode

---

## Most Likely Cause

### Scenario A: Fallback Not Working

**Evidence**:
- Seed logs show config created with `user_id="default_user"` ✅
- Fallback code exists in init.py ✅
- BUT user still gets generic config ❌

**Possible causes**:
1. **Encryption mismatch**: Config can't be decrypted (we saw this before!)
   - Solution: Re-seed with Railway's FERNET_KEY (already done)
2. **Weaviate query fails**: Network timeout, permission issue
3. **Config not saved properly**: Seed script succeeds but data not in Weaviate

### Scenario B: Frontend State Issue

**Evidence**:
- Chrome works (has old localStorage from local dev)
- Safari/new device fails (fresh localStorage)

**Possible causes**:
1. **User ID generation**: Frontend generates different user_id format
2. **Config loading timing**: Race condition between initialize_user and load_config
3. **Frontend caching**: Old frontend JavaScript cached, new backend deployed

---

## Debugging Steps

### Step 1: Verify Default Config in Weaviate

Run on Railway:
```bash
railway run python3 <<EOF
import asyncio
from elysia.util.client import ClientManager
from weaviate.classes.query import Filter

async def check():
    client_manager = ClientManager()
    async with client_manager.connect_to_async_client() as client:
        collection = client.collections.get("ELYSIA_CONFIG__")
        configs = await collection.query.fetch_objects(
            filters=Filter.all_of([
                Filter.by_property("default").equal(True),
                Filter.by_property("user_id").equal("default_user"),
            ])
        )
        print(f"Found {len(configs.objects)} default configs")
        if configs.objects:
            props = configs.objects[0].properties
            print(f"Name: {props.get('name')}")
            print(f"Bootstrappers: {props.get('feature_bootstrappers')}")
    await client_manager.close_clients()

asyncio.run(check())
EOF
```

### Step 2: Check Railway Logs for Init Requests

Filter for: `initialise_user` and look for:
- What user_id is being sent?
- Does fallback trigger?
- Does config load succeed?

### Step 3: Test Frontend Cache

**Clear Safari completely**:
1. Safari → Settings → Privacy → Manage Website Data → Remove All
2. Reload `https://hva-elysia.up.railway.app`
3. Open Dev Tools → Network tab
4. Watch for `/init/user/{user_id}` request
5. Check response: `config` should have `feature_bootstrappers: ["vsm_smido"]`

---

## Suspected Root Causes (Priority Order)

### 1. **Frontend Build Cache** (Most Likely)
**Problem**: Old frontend JavaScript cached in browser/CDN  
**Evidence**: Static file serving works for diagrams, but app logic doesn't match backend

**Test**:
```bash
# Check if static frontend matches latest build
curl https://hva-elysia.up.railway.app/static/index.html | grep "buildId"
```

**Fix**: Hard refresh (Cmd+Shift+R) or rebuild frontend

### 2. **Seed Script Encryption Mismatch**
**Problem**: Config saved but can't be decrypted  
**Evidence**: We've seen "Invalid token" warnings in logs

**Test**: Check Railway logs for `Invalid token for default config`

**Fix**: Already implemented (auto-reseed on encryption fail)

### 3. **WEAVIATE_IS_LOCAL Environment Variable**
**Problem**: App tries to connect to localhost Weaviate instead of cloud  
**Evidence**: Would explain why cloud config not found

**Test**: Check Railway env vars for WEAVIATE_IS_LOCAL

**Fix**: Ensure `WEAVIATE_IS_LOCAL=False` on Railway

---

## Immediate Actions Required

### Action 1: Verify Railway Environment Variables

Run: `railway variables`

**Must have**:
```
WCD_URL=mrslrqo5rzkqafoqgbvdw.c0.europe-west3.gcp.weaviate.cloud
WCD_API_KEY=(encrypted)
WEAVIATE_IS_LOCAL=False  ← CRITICAL
BASE_MODEL=gemini-2.5-flash
COMPLEX_MODEL=gemini-2.5-pro
BASE_PROVIDER=gemini
COMPLEX_PROVIDER=gemini
```

### Action 2: Check Default Config Exists

Railway run:
```bash
railway run python3 -c "
import asyncio
from elysia.util.client import ClientManager
from weaviate.classes.query import Filter

async def check():
    cm = ClientManager()
    async with cm.connect_to_async_client() as client:
        coll = client.collections.get('ELYSIA_CONFIG__')
        res = await coll.query.fetch_objects(
            filters=Filter.by_property('user_id').equal('default_user')
        )
        print(f'Configs: {len(res.objects)}')
        for obj in res.objects:
            p = obj.properties
            print(f\"Name: {p.get('name')}, Bootstrappers: {p.get('feature_bootstrappers')}\")
    await cm.close_clients()

asyncio.run(check())
"
```

### Action 3: Test Frontend State Across Browsers

1. Chrome (working): Open Dev Tools → Application → Local Storage
   - Note the `user_id` value
2. Safari (failing): Same check
   - Is `user_id` different?
   - Does `/init/user/{user_id}` return correct config?

---

## Expected vs Actual

### Expected Flow (ANY Browser):
1. Frontend generates `user_id` (any value)
2. Calls `/init/user/{user_id}`
3. Backend checks for user-specific config (not found)
4. **Fallback to `default_user` config** (should find VSM config)
5. Returns VSM config with `feature_bootstrappers: ["vsm_smido"]`
6. VSM tools loaded ✅

### Actual Flow (Safari):
1. Frontend generates `user_id = "xyz789"`
2. Calls `/init/user/xyz789`
3. Backend checks for user-specific config (not found)
4. **Fallback fails or returns generic config**
5. Returns Elysia default (no bootstrappers)
6. No tools loaded ❌

**The gap**: Why does fallback fail in Safari but not Chrome?

---

## Hypothesis: Frontend Config File Dependency

**Code** (elysia/api/services/user.py line 174):
```python
fe_config = await load_frontend_config_from_file(user_id, logger)
```

**This loads from**: `elysia/api/user_configs/frontend_config_{user_id}.json`

**On Railway**: This directory is EMPTY (no persistent filesystem)  
**Result**: Always returns default FrontendConfig()

**Potential issue**: If frontend_config affects Weaviate connection, it could break config loading.

---

## Quick Diagnosis Command

Run this to see exact state:

```bash
railway logs --filter "initialise_user" | tail -100
```

Look for:
- What `user_id` values are being used?
- Does "Using default config" appear in logs?
- Any "Could not connect to Weaviate" errors?

---

## Summary

**Most Likely**: Frontend cache issue - old JavaScript in browser  
**Secondary**: Config encryption/decryption mismatch per browser  
**Tertiary**: localStorage security restrictions in Safari

**Next Action**: Need to see Railway logs filtering for `initialise_user` to see what's happening during the failing Safari request.

