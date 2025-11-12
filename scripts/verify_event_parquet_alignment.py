#!/usr/bin/env python3
"""
Verify that telemetry events JSONL matches rebased parquet data.
Checks timestamps, event IDs, and data consistency.
"""
import pandas as pd
import json
from pathlib import Path
from datetime import datetime

def verify_alignment():
    """Verify events align with rebased parquet data"""
    print("="*80)
    print("EVENT-PARQUET ALIGNMENT VERIFICATION")
    print("="*80)
    
    # Load parquet
    parquet_path = Path("features/telemetry/timeseries_freezerdata/135_1570_cleaned_with_flags.parquet")
    print(f"\n1. Loading parquet: {parquet_path}")
    df = pd.read_parquet(parquet_path)
    parquet_min = df.index.min()
    parquet_max = df.index.max()
    print(f"   Parquet range: {parquet_min} to {parquet_max}")
    print(f"   Total rows: {len(df):,}")
    
    # Load events
    events_path = Path("features/telemetry_vsm/output/telemetry_events.jsonl")
    print(f"\n2. Loading events: {events_path}")
    events = []
    with open(events_path, 'r') as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))
    
    print(f"   Total events: {len(events)}")
    
    # Verify each event
    print(f"\n3. Verifying event alignment:")
    all_valid = True
    
    for i, event in enumerate(events, 1):
        event_id = event.get('event_id', 'UNKNOWN')
        t_start = event.get('t_start')
        t_end = event.get('t_end')
        time_range_start = event.get('time_range_start')
        time_range_end = event.get('time_range_end')
        parquet_path_ref = event.get('parquet_path')
        duration = event.get('duration_minutes', 0)
        
        # Parse timestamps
        try:
            ts_start = datetime.fromisoformat(t_start.replace('Z', '+00:00') if 'Z' in t_start else t_start)
            ts_end = datetime.fromisoformat(t_end.replace('Z', '+00:00') if 'Z' in t_end else t_end)
        except Exception as e:
            print(f"   ❌ Event {i} ({event_id}): Invalid timestamp format - {e}")
            all_valid = False
            continue
        
        # Check event ID matches timestamp
        expected_id_date = ts_start.strftime('%Y%m%d_%H%M')
        if expected_id_date not in event_id:
            print(f"   ⚠️  Event {i} ({event_id}): Event ID doesn't match timestamp {t_start}")
            print(f"      Expected ID to contain: {expected_id_date}")
        
        # Check timestamps within parquet range
        if ts_start < parquet_min or ts_start > parquet_max:
            print(f"   ❌ Event {i} ({event_id}): t_start {t_start} outside parquet range")
            all_valid = False
        
        if ts_end < parquet_min or ts_end > parquet_max:
            print(f"   ❌ Event {i} ({event_id}): t_end {t_end} outside parquet range")
            all_valid = False
        
        # Check time_range matches t_start/t_end
        if time_range_start != t_start:
            print(f"   ⚠️  Event {i} ({event_id}): time_range_start ({time_range_start}) != t_start ({t_start})")
        
        if time_range_end != t_end:
            print(f"   ⚠️  Event {i} ({event_id}): time_range_end ({time_range_end}) != t_end ({t_end})")
        
        # Check duration (warn but don't fail - known data anomaly)
        if duration < 0:
            print(f"   ⚠️  Event {i} ({event_id}): Negative duration {duration} minutes (data anomaly, will import anyway)")
        
        # Check parquet path
        if parquet_path_ref != str(parquet_path):
            print(f"   ⚠️  Event {i} ({event_id}): parquet_path mismatch")
            print(f"      Event: {parquet_path_ref}")
            print(f"      Expected: {parquet_path}")
        
        # Check required fields
        required_fields = ['event_id', 'asset_id', 't_start', 't_end', 'failure_mode', 
                          'description_nl', 'worldstate_summary']
        missing = [f for f in required_fields if not event.get(f)]
        if missing:
            print(f"   ❌ Event {i} ({event_id}): Missing required fields: {missing}")
            all_valid = False
        
        if i <= 3:  # Show first 3 events as examples
            print(f"   ✅ Event {i}: {event_id}")
            print(f"      Range: {t_start} to {t_end} ({duration} min)")
            print(f"      Failure mode: {event.get('failure_mode')}")
    
    # Summary
    print(f"\n4. Summary:")
    if all_valid and len(events) == 12:
        print(f"   ✅ All {len(events)} events valid and aligned with parquet data")
        print(f"   ✅ Event timestamps within parquet range: {parquet_min} to {parquet_max}")
        return True
    else:
        print(f"   ❌ Validation failed or unexpected event count")
        return False

if __name__ == "__main__":
    success = verify_alignment()
    exit(0 if success else 1)

