#!/usr/bin/env python3
"""
Cross-reference verification: Verify Weaviate events match rebased parquet data.
"""
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.query import Filter
import os
import json
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

weaviate_url = os.environ.get("WEAVIATE_URL") or os.environ.get("WCD_URL")
weaviate_api_key = os.environ.get("WEAVIATE_API_KEY") or os.environ.get("WCD_API_KEY")

def main():
    print("="*80)
    print("CROSS-REFERENCE VERIFICATION")
    print("="*80)
    
    # Load parquet
    parquet_path = Path("features/telemetry/timeseries_freezerdata/135_1570_cleaned_with_flags.parquet")
    df = pd.read_parquet(parquet_path)
    parquet_min = df.index.min()
    parquet_max = df.index.max()
    print(f"\n1. Parquet data:")
    print(f"   Range: {parquet_min} to {parquet_max}")
    print(f"   Rows: {len(df):,}")
    
    # Load events JSONL
    events_path = Path("features/telemetry_vsm/output/telemetry_events.jsonl")
    with open(events_path, 'r') as f:
        jsonl_events = [json.loads(line) for line in f if line.strip()]
    
    print(f"\n2. Events JSONL:")
    print(f"   Count: {len(jsonl_events)}")
    print(f"   First: {jsonl_events[0].get('event_id')} ({jsonl_events[0].get('t_start')})")
    print(f"   Last: {jsonl_events[-1].get('event_id')} ({jsonl_events[-1].get('t_end')})")
    
    # Connect to Weaviate
    print(f"\n3. Weaviate collection:")
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=weaviate_url,
        auth_credentials=Auth.api_key(weaviate_api_key)
    )
    
    try:
        collection = client.collections.get("VSM_TelemetryEvent")
        weaviate_events = collection.query.fetch_objects(limit=100)
        
        print(f"   Count: {len(weaviate_events.objects)}")
        
        if len(weaviate_events.objects) > 0:
            print(f"   First: {weaviate_events.objects[0].properties.get('event_id')} ({weaviate_events.objects[0].properties.get('t_start')})")
            print(f"   Last: {weaviate_events.objects[-1].properties.get('event_id')} ({weaviate_events.objects[-1].properties.get('t_end')})")
        
        # Cross-reference check
        print(f"\n4. Cross-reference verification:")
        
        # Check counts match
        if len(jsonl_events) == len(weaviate_events.objects):
            print(f"   ✅ Event counts match: {len(jsonl_events)}")
        else:
            print(f"   ❌ Event count mismatch: JSONL={len(jsonl_events)}, Weaviate={len(weaviate_events.objects)}")
        
        # Check event IDs match
        jsonl_ids = {e.get('event_id') for e in jsonl_events}
        weaviate_ids = {e.properties.get('event_id') for e in weaviate_events.objects}
        
        if jsonl_ids == weaviate_ids:
            print(f"   ✅ Event IDs match between JSONL and Weaviate")
        else:
            missing_in_weaviate = jsonl_ids - weaviate_ids
            extra_in_weaviate = weaviate_ids - jsonl_ids
            if missing_in_weaviate:
                print(f"   ❌ Events in JSONL but not in Weaviate: {missing_in_weaviate}")
            if extra_in_weaviate:
                print(f"   ❌ Events in Weaviate but not in JSONL: {extra_in_weaviate}")
        
        # Check timestamps match (match by event_id)
        print(f"\n5. Timestamp verification:")
        all_match = True
        checked = 0
        for weaviate_event in weaviate_events.objects:
            event_id = weaviate_event.properties.get('event_id')
            jsonl_event = next((e for e in jsonl_events if e.get('event_id') == event_id), None)
            
            if jsonl_event:
                w_t_start = weaviate_event.properties.get('t_start')
                j_t_start = jsonl_event.get('t_start')
                w_t_end = weaviate_event.properties.get('t_end')
                j_t_end = jsonl_event.get('t_end')
                
                if w_t_start == j_t_start and w_t_end == j_t_end:
                    if checked < 5:  # Show first 5 matches
                        print(f"   ✅ {event_id}: Timestamps match")
                    checked += 1
                else:
                    print(f"   ❌ {event_id}: Timestamp mismatch")
                    print(f"      Weaviate: {w_t_start} to {w_t_end}")
                    print(f"      JSONL: {j_t_start} to {j_t_end}")
                    all_match = False
                    checked += 1
        
        if all_match:
            print(f"   ✅ All {len(weaviate_events.objects)} events have matching timestamps")
        
        # Verify all timestamps within parquet range
        print(f"\n6. Parquet range verification:")
        all_in_range = True
        for weaviate_event in weaviate_events.objects:
            t_start = datetime.fromisoformat(weaviate_event.properties.get('t_start').replace('Z', '+00:00') if 'Z' in weaviate_event.properties.get('t_start') else weaviate_event.properties.get('t_start'))
            t_end = datetime.fromisoformat(weaviate_event.properties.get('t_end').replace('Z', '+00:00') if 'Z' in weaviate_event.properties.get('t_end') else weaviate_event.properties.get('t_end'))
            
            if t_start < parquet_min or t_start > parquet_max:
                print(f"   ❌ {weaviate_event.properties.get('event_id')}: t_start {t_start} outside parquet range")
                all_in_range = False
            if t_end < parquet_min or t_end > parquet_max:
                print(f"   ❌ {weaviate_event.properties.get('event_id')}: t_end {t_end} outside parquet range")
                all_in_range = False
        
        if all_in_range:
            print(f"   ✅ All event timestamps within parquet range")
        
        # Summary
        print(f"\n7. Summary:")
        if len(jsonl_events) == len(weaviate_events.objects) and jsonl_ids == weaviate_ids and all_match and all_in_range:
            print(f"   ✅ All verifications passed!")
            print(f"   ✅ JSONL and Weaviate are synchronized")
            print(f"   ✅ All timestamps match rebased parquet data")
            return True
        else:
            print(f"   ❌ Some verifications failed")
            return False
            
    finally:
        client.close()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

