#!/usr/bin/env python3
"""
Update VSM_TelemetryEvent collection in Weaviate Cloud with rebased telemetry events.

Adapted from features/telemetry_vsm/src/import_telemetry_weaviate.py
This script:
1. Verifies events JSONL matches rebased parquet data
2. Deletes all existing events from VSM_TelemetryEvent
3. Re-imports events from the regenerated JSONL file (with new timestamps)
4. Verifies import success

Run this after rebasing telemetry parquet files and regenerating events.

Usage:
    python3 features/telemetry_vsm/src/update_telemetry_events_weaviate.py [--dry-run]
"""
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.query import Filter
import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime

# Load environment variables
load_dotenv()

weaviate_url = os.environ.get("WEAVIATE_URL") or os.environ.get("WCD_URL")
weaviate_api_key = os.environ.get("WEAVIATE_API_KEY") or os.environ.get("WCD_API_KEY")

if not weaviate_url or not weaviate_api_key:
    print("❌ Error: WEAVIATE_URL/WCD_URL and WEAVIATE_API_KEY/WCD_API_KEY must be set in .env")
    exit(1)

def verify_event_parquet_alignment():
    """Verify events JSONL matches rebased parquet data"""
    print("\n" + "="*80)
    print("PRE-FLIGHT VERIFICATION: Event-Parquet Alignment")
    print("="*80)
    
    # Load parquet
    parquet_path = Path("features/telemetry/timeseries_freezerdata/135_1570_cleaned_with_flags.parquet")
    if not parquet_path.exists():
        print(f"❌ Error: Parquet file not found: {parquet_path}")
        return False
    
    df = pd.read_parquet(parquet_path)
    parquet_min = df.index.min()
    parquet_max = df.index.max()
    print(f"✅ Parquet range: {parquet_min} to {parquet_max}")
    
    # Load events
    events_path = Path("features/telemetry_vsm/output/telemetry_events.jsonl")
    if not events_path.exists():
        print(f"❌ Error: Events JSONL not found: {events_path}")
        print("   Run: python3 features/telemetry_vsm/src/detect_events.py")
        return False
    
    events = []
    with open(events_path, 'r') as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))
    
    print(f"✅ Loaded {len(events)} events from JSONL")
    
    # Verify timestamps
    all_valid = True
    for i, event in enumerate(events, 1):
        t_start = event.get('t_start')
        t_end = event.get('t_end')
        
        try:
            ts_start = datetime.fromisoformat(t_start.replace('Z', '+00:00') if 'Z' in t_start else t_start)
            ts_end = datetime.fromisoformat(t_end.replace('Z', '+00:00') if 'Z' in t_end else t_end)
        except Exception as e:
            print(f"❌ Event {i}: Invalid timestamp format - {e}")
            all_valid = False
            continue
        
        if ts_start < parquet_min or ts_start > parquet_max:
            print(f"❌ Event {i}: t_start {t_start} outside parquet range")
            all_valid = False
        
        if ts_end < parquet_min or ts_end > parquet_max:
            print(f"❌ Event {i}: t_end {t_end} outside parquet range")
            all_valid = False
    
    if all_valid:
        print(f"✅ All events aligned with parquet data")
        return True
    else:
        print(f"❌ Event-parquet alignment verification failed")
        return False

def main():
    """Main update process"""
    # Check for dry-run mode
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv
    
    print("="*80)
    print("WEAVIATE TELEMETRY EVENTS UPDATE")
    if dry_run:
        print("🔍 DRY-RUN MODE (no changes will be made)")
    print("="*80)
    print("Updating VSM_TelemetryEvent collection with rebased telemetry events")
    print("New date range: 2024-07-21 to 2025-01-09")
    print()
    
    # Step 1: Pre-flight verification
    if not verify_event_parquet_alignment():
        print("\n❌ Pre-flight verification failed. Aborting.")
        exit(1)
    
    # Step 2: Connect to Weaviate Cloud
    print("\n" + "="*80)
    print("STEP 1: Connecting to Weaviate Cloud")
    print("="*80)
    
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=weaviate_url,
        auth_credentials=Auth.api_key(weaviate_api_key)
    )
    print(f"✅ Weaviate client ready: {client.is_ready()}")
    
    try:
        # Step 3: Get existing collection (don't create)
        print("\n" + "="*80)
        print("STEP 2: Getting existing collection")
        print("="*80)
        
        if not client.collections.exists("VSM_TelemetryEvent"):
            print("❌ Error: VSM_TelemetryEvent collection does not exist!")
            print("   Run features/telemetry_vsm/src/import_telemetry_weaviate.py first to create it.")
            exit(1)
        
        collection = client.collections.get("VSM_TelemetryEvent")
        print("✅ Collection exists")
        
        # Step 4: Count and delete existing events
        print("\n" + "="*80)
        print("STEP 3: Deleting existing events")
        print("="*80)
        
        total_before = collection.aggregate.over_all(total_count=True).total_count
        print(f"Current events in collection: {total_before}")
        
        if total_before > 0:
            # Fetch all objects to get their UUIDs
            print("Fetching all event UUIDs...")
            all_events = collection.query.fetch_objects(limit=1000)  # Should be enough for 12 events
            
            if dry_run:
                print(f"🔍 DRY-RUN: Would delete {len(all_events.objects)} events")
                print("   Sample events that would be deleted:")
                for i, obj in enumerate(all_events.objects[:3], 1):
                    props = obj.properties
                    print(f"     {i}. {props.get('event_id')}: {props.get('t_start')} to {props.get('t_end')}")
            else:
                if len(all_events.objects) == total_before:
                    print(f"Deleting {len(all_events.objects)} events...")
                    for i, obj in enumerate(all_events.objects, 1):
                        collection.data.delete_by_id(obj.uuid)
                        if i % 5 == 0 or i == len(all_events.objects):
                            print(f"  Deleted {i}/{len(all_events.objects)}...")
                    
                    print(f"✅ Deleted {len(all_events.objects)} events")
                else:
                    print(f"⚠️  Warning: Found {len(all_events.objects)} events but total count is {total_before}")
                    print("   Deleting fetched events...")
                    for obj in all_events.objects:
                        collection.data.delete_by_id(obj.uuid)
                    print(f"✅ Deleted {len(all_events.objects)} events")
                    if total_before > len(all_events.objects):
                        print(f"   Note: {total_before - len(all_events.objects)} events may remain. Run script again if needed.")
        else:
            print("✅ Collection is already empty")
        
        # Verify deletion
        total_after = collection.aggregate.over_all(total_count=True).total_count
        print(f"Events remaining: {total_after}")
        
        if total_after > 0:
            print(f"⚠️  Warning: {total_after} events still remain.")
        
        # Step 5: Load and import new events
        print("\n" + "="*80)
        print("STEP 4: Importing rebased events")
        print("="*80)
        
        events_path = Path("features/telemetry_vsm/output/telemetry_events.jsonl")
        with open(events_path, "r") as f:
            data = [json.loads(line) for line in f if line.strip()]
        
        print(f"Loaded {len(data)} events from {events_path}")
        
        # Show sample of new timestamps
        if data:
            print("\nSample of new timestamps:")
            for i, event in enumerate(data[:3], 1):
                print(f"  {i}. {event.get('event_id')}: {event.get('t_start')} to {event.get('t_end')}")
        
        # Batch import (reuse logic from original import script)
        if dry_run:
            print(f"\n🔍 DRY-RUN: Would import {len(data)} events")
            print("   Sample events that would be imported:")
            for i, event in enumerate(data[:3], 1):
                print(f"     {i}. {event.get('event_id')}: {event.get('t_start')} to {event.get('t_end')}")
        else:
            print(f"\nImporting {len(data)} events...")
            with collection.batch.fixed_size(batch_size=200) as batch:
                for i, item in enumerate(data, 1):
                    batch.add_object(item)
                    
                    if batch.number_errors > 10:
                        print("❌ Stopped due to excessive errors.")
                        break
                    
                    if i % 5 == 0 or i == len(data):
                        print(f"  Imported {i}/{len(data)}...")
            
            # Error handling
            failed = collection.batch.failed_objects
            if failed:
                print(f"\n❌ Failed: {len(failed)} objects")
                print(f"   First error: {failed[0]}")
                exit(1)
            else:
                print(f"\n✅ All {len(data)} events imported successfully!")
        
        # Step 6: Post-import verification
        if not dry_run:
            print("\n" + "="*80)
            print("STEP 5: Post-Import Verification")
            print("="*80)
            
            total = collection.aggregate.over_all(total_count=True).total_count
            print(f"Total objects in VSM_TelemetryEvent: {total}")
            
            if total != len(data):
                print(f"⚠️  Warning: Expected {len(data)} events, found {total}")
        
            # Test queries
            print("\nTesting queries:")
            
            # Check for events with new date range
            recent_events = collection.query.fetch_objects(
                filters=Filter.by_property("t_start").greater_than("2024-07-21"),
                limit=5
            )
            print(f"  ✅ Events after 2024-07-21: {len(recent_events.objects)}")
            
            if recent_events.objects:
                print("  Sample recent event:")
                sample = recent_events.objects[0]
                print(f"    - {sample.properties.get('event_id')}: {sample.properties.get('t_start')} to {sample.properties.get('t_end')}")
            
            # Test failure mode filter
            critical = collection.query.fetch_objects(
                filters=Filter.by_property("severity").equal("critical"),
                limit=1
            )
            print(f"  ✅ Critical events: {len(critical.objects)}")
            
            # Test frozen evaporator filter
            frozen = collection.query.fetch_objects(
                filters=Filter.by_property("failure_modes").contains_any(["ingevroren_verdamper"]),
                limit=1
            )
            print(f"  ✅ Frozen evaporator events: {len(frozen.objects)}")
            
            # Verify event IDs contain new dates
            all_events_new = collection.query.fetch_objects(limit=12)
            old_date_count = sum(1 for e in all_events_new.objects 
                               if e.properties.get('event_id', '').startswith('evt_2022') 
                               or e.properties.get('event_id', '').startswith('evt_2023'))
            new_date_count = sum(1 for e in all_events_new.objects 
                                if e.properties.get('event_id', '').startswith('evt_2024') 
                                or e.properties.get('event_id', '').startswith('evt_2025'))
            
            print(f"\nEvent ID verification:")
            print(f"  Events with old dates (2022-2023): {old_date_count}")
            print(f"  Events with new dates (2024-2025): {new_date_count}")
            
            if old_date_count > 0:
                print(f"  ⚠️  Warning: {old_date_count} events still have old dates")
            else:
                print(f"  ✅ All events have new dates")
            
            print("\n✅ Weaviate update complete!")
            print("\nNext steps:")
            print("  1. Test query_telemetry_events tool to verify it returns updated timestamps")
            print("  2. Verify frontend displays correct dates")
        else:
            print("\n🔍 DRY-RUN complete. Run without --dry-run to perform actual update.")
        
    finally:
        client.close()

if __name__ == "__main__":
    main()

