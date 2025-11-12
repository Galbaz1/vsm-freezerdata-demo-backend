#!/usr/bin/env python3
"""
Update VSM_TelemetryEvent collection in Weaviate with rebased telemetry events.

This script:
1. Deletes all existing events from VSM_TelemetryEvent
2. Re-imports events from the regenerated JSONL file (with new timestamps)

Run this after rebasing telemetry parquet files and regenerating events.
"""
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.query import Filter
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

weaviate_url = os.environ.get("WEAVIATE_URL") or os.environ.get("WCD_URL")
weaviate_api_key = os.environ.get("WEAVIATE_API_KEY") or os.environ.get("WCD_API_KEY")

if not weaviate_url or not weaviate_api_key:
    print("❌ Error: WEAVIATE_URL/WCD_URL and WEAVIATE_API_KEY/WCD_API_KEY must be set in .env")
    exit(1)

# Connect to Weaviate Cloud
print("Connecting to Weaviate...")
client = weaviate.connect_to_weaviate_cloud(
    cluster_url=weaviate_url,
    auth_credentials=Auth.api_key(weaviate_api_key)
)
print(f"✅ Weaviate client ready: {client.is_ready()}")

try:
    # Get collection (don't create, it should already exist)
    if not client.collections.exists("VSM_TelemetryEvent"):
        print("❌ Error: VSM_TelemetryEvent collection does not exist!")
        print("   Run features/telemetry_vsm/src/import_telemetry_weaviate.py first to create it.")
        exit(1)
    
    collection = client.collections.get("VSM_TelemetryEvent")
    
    # Step 1: Delete all existing events
    print("\n" + "="*80)
    print("STEP 1: Deleting existing events")
    print("="*80)
    
    # Get count before deletion
    total_before = collection.aggregate.over_all(total_count=True).total_count
    print(f"Current events in collection: {total_before}")
    
    if total_before > 0:
        # Fetch all objects to get their UUIDs
        print("Fetching all event UUIDs...")
        all_events = collection.query.fetch_objects(limit=1000)  # Adjust if >1000 events
        
        if len(all_events.objects) == total_before:
            # Delete all objects
            print(f"Deleting {len(all_events.objects)} events...")
            for i, obj in enumerate(all_events.objects, 1):
                collection.data.delete_by_id(obj.uuid)
                if i % 10 == 0:
                    print(f"  Deleted {i}/{len(all_events.objects)}...")
            
            print(f"✅ Deleted {len(all_events.objects)} events")
        else:
            print(f"⚠️  Warning: Found {len(all_events.objects)} events but total count is {total_before}")
            print("   Deleting fetched events...")
            for obj in all_events.objects:
                collection.data.delete_by_id(obj.uuid)
            print(f"✅ Deleted {len(all_events.objects)} events")
            print("   Note: If total count > fetched, run this script again to delete remaining events")
    else:
        print("✅ Collection is already empty")
    
    # Verify deletion
    total_after = collection.aggregate.over_all(total_count=True).total_count
    print(f"Events remaining: {total_after}")
    
    if total_after > 0:
        print(f"⚠️  Warning: {total_after} events still remain. You may need to run this script again.")
    
    # Step 2: Re-import events from regenerated JSONL
    print("\n" + "="*80)
    print("STEP 2: Importing rebased events")
    print("="*80)
    
    jsonl_path = "features/telemetry_vsm/output/telemetry_events.jsonl"
    if not os.path.exists(jsonl_path):
        print(f"❌ Error: JSONL file not found: {jsonl_path}")
        print("   Run features/telemetry_vsm/src/detect_events.py first to regenerate events.")
        exit(1)
    
    # Load regenerated events
    with open(jsonl_path, "r") as f:
        data = [json.loads(line) for line in f if line.strip()]
    
    print(f"Loaded {len(data)} events from {jsonl_path}")
    
    # Show sample of new timestamps
    if data:
        print("\nSample of new timestamps:")
        for i, event in enumerate(data[:3], 1):
            print(f"  {i}. {event.get('event_id')}: {event.get('t_start')} to {event.get('t_end')}")
    
    # Batch import
    print(f"\nImporting {len(data)} events...")
    with collection.batch.fixed_size(batch_size=200) as batch:
        for i, item in enumerate(data, 1):
            batch.add_object(item)
            
            if batch.number_errors > 10:
                print("❌ Stopped due to excessive errors.")
                break
            
            if i % 10 == 0:
                print(f"  Imported {i}/{len(data)}...")
    
    # Error handling
    failed = collection.batch.failed_objects
    if failed:
        print(f"\n❌ Failed: {len(failed)} objects")
        print(f"   First error: {failed[0]}")
    else:
        print(f"\n✅ All {len(data)} events imported successfully!")
    
    # Step 3: Verify
    print("\n" + "="*80)
    print("STEP 3: Verification")
    print("="*80)
    
    total = collection.aggregate.over_all(total_count=True).total_count
    print(f"Total objects in VSM_TelemetryEvent: {total}")
    
    # Test queries
    print("\nTesting queries:")
    
    # Check for events with new date range
    recent_events = collection.query.fetch_objects(
        filters=Filter.by_property("t_start").greater_than("2024-07-21"),
        limit=5
    )
    print(f"  Events after 2024-07-21: {len(recent_events.objects)}")
    
    if recent_events.objects:
        print("  Sample recent event:")
        sample = recent_events.objects[0]
        print(f"    - {sample.properties.get('event_id')}: {sample.properties.get('t_start')} to {sample.properties.get('t_end')}")
    
    critical = collection.query.fetch_objects(
        filters=Filter.by_property("severity").equal("critical"),
        limit=1
    )
    print(f"  Critical events: {len(critical.objects)}")
    
    frozen = collection.query.fetch_objects(
        filters=Filter.by_property("failure_modes").contains_any(["ingevroren_verdamper"]),
        limit=1
    )
    print(f"  Frozen evaporator events: {len(frozen.objects)}")
    
    print("\n✅ Weaviate update complete!")
    print("\nNext steps:")
    print("  1. Test query_telemetry_events tool to verify it returns updated timestamps")
    print("  2. Verify frontend displays correct dates")

finally:
    client.close()

