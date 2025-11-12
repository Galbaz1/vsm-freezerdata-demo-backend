# Weaviate Update Required for Telemetry Rebase

**Status**: ⚠️ **NOT YET UPDATED**  
**Date**: November 12, 2025

## Summary

The telemetry parquet files and event JSONL have been rebased with new timestamps (2024-07-21 to 2026-01-01), but **Weaviate has NOT been updated yet**. The `VSM_TelemetryEvent` collection still contains events with old timestamps (2022-2024).

## What Needs Updating

### Collection: `VSM_TelemetryEvent`

**Fields that contain timestamps**:
- `t_start` - Event start timestamp (TEXT)
- `t_end` - Event end timestamp (TEXT)  
- `time_range_start` - Time range start (TEXT)
- `time_range_end` - Time range end (TEXT)
- `event_id` - Contains date (e.g., `evt_20221020_1602`)

**Current State**:
- Contains 12 events with old timestamps (2022-10-20 to 2023-04-10)
- Event IDs like `evt_20221020_1602`, `evt_20221027_1556`, etc.

**Required State**:
- Should contain 12 events with new timestamps (2024-07-21 to 2025-01-09)
- Event IDs like `evt_20240721_1403`, `evt_20240728_1352`, etc.

## Why Update is Critical

1. **Tool Queries**: `query_telemetry_events` tool queries Weaviate for historical incidents
2. **Timestamp Filters**: Tools may filter by `t_start`/`t_end` dates
3. **Semantic Search**: Vector search uses `description_nl` and `worldstate_summary` which may reference dates
4. **Data Consistency**: Parquet files, JSONL, and Weaviate should all have matching timestamps

## How to Update

### Option 1: Delete and Re-import (Recommended)

Use the provided update script:

```bash
conda activate vsm-hva
python3 scripts/update_weaviate_telemetry_events.py
```

**What it does**:
1. Connects to Weaviate
2. Deletes all existing events from `VSM_TelemetryEvent`
3. Re-imports events from `features/telemetry_vsm/output/telemetry_events.jsonl` (already regenerated)
4. Verifies import and tests queries

**Prerequisites**:
- `.env` file must have `WEAVIATE_URL`/`WCD_URL` and `WEAVIATE_API_KEY`/`WCD_API_KEY`
- `features/telemetry_vsm/output/telemetry_events.jsonl` must exist (already regenerated ✅)

### Option 2: Manual Update via Weaviate Console

1. Open Weaviate Console
2. Navigate to `VSM_TelemetryEvent` collection
3. Delete all objects
4. Run `features/telemetry_vsm/src/import_telemetry_weaviate.py` (but modify it to not create collection)

**Note**: The original import script uses `collection.create()` which will fail if collection exists. The update script handles this correctly.

## Verification

After updating, verify:

```python
# Quick check via Python
from elysia.util.client import ClientManager
from weaviate.classes.query import Filter

async def check():
    async with ClientManager().connect_to_async_client() as client:
        collection = client.collections.get("VSM_TelemetryEvent")
        
        # Check for new timestamps
        recent = await collection.query.fetch_objects(
            filters=Filter.by_property("t_start").greater_than("2024-07-21"),
            limit=5
        )
        print(f"Events after 2024-07-21: {len(recent.objects)}")
        
        if recent.objects:
            sample = recent.objects[0]
            print(f"Sample: {sample.properties.get('event_id')} - {sample.properties.get('t_start')}")

import asyncio
asyncio.run(check())
```

Or test via the `query_telemetry_events` tool in the frontend.

## Impact if Not Updated

If Weaviate is not updated:
- ❌ `query_telemetry_events` tool returns events with old timestamps (2022-2024)
- ❌ Date-based filters won't work correctly
- ❌ Inconsistency between parquet data (2024-2026) and Weaviate events (2022-2024)
- ❌ Frontend may display confusing date ranges
- ✅ Tools that read directly from parquet (like `compute_worldstate`) will work correctly

## Files Involved

- **Update Script**: `scripts/update_weaviate_telemetry_events.py` (NEW - created)
- **Import Script**: `features/telemetry_vsm/src/import_telemetry_weaviate.py` (original - creates collection)
- **Event JSONL**: `features/telemetry_vsm/output/telemetry_events.jsonl` (already regenerated ✅)
- **Collection**: `VSM_TelemetryEvent` in Weaviate Cloud (needs update ⚠️)

## Next Steps

1. ✅ Parquet files rebased
2. ✅ Events JSONL regenerated  
3. ⚠️ **Run `scripts/update_weaviate_telemetry_events.py` to update Weaviate**
4. ✅ Verify queries return correct timestamps
5. ✅ Test frontend displays correct dates

