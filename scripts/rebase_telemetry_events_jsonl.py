#!/usr/bin/env python3
"""
Rebase telemetry_events.jsonl timestamps to align with rebased parquet data.
Shifts timestamps +639 days (Oct 2022 → Jul 2024, Apr 2023 → Jan 2025)

This makes the 12 reference "uit balans" incidents align with the current parquet timerange.
"""
import json
from datetime import datetime, timedelta
from pathlib import Path
import shutil

SHIFT_DAYS = 639  # Same as parquet rebase

def main():
    input_file = Path("features/telemetry_vsm/output/telemetry_events.jsonl")
    backup_file = input_file.with_suffix(".jsonl.backup")
    output_file = input_file
    
    print("=" * 80)
    print("Rebasing telemetry_events.jsonl")
    print("=" * 80)
    
    # Backup if not exists
    if not backup_file.exists():
        shutil.copy(input_file, backup_file)
        print(f"✅ Backup created: {backup_file}")
    else:
        print(f"⚠️  Backup already exists: {backup_file}")
    
    # Load events
    with open(input_file) as f:
        events = [json.loads(line) for line in f if line.strip()]
    
    print(f"\nLoaded {len(events)} events")
    
    # Show original range
    original_times = [e.get('t_start') or e.get('timestamp') for e in events if e.get('t_start') or e.get('timestamp')]
    if original_times:
        print(f"Original range: {min(original_times)} → {max(original_times)}")
    
    # Rebase timestamps
    delta = timedelta(days=SHIFT_DAYS)
    rebased_count = 0
    
    for event in events:
        # Update all timestamp fields
        for field in ['t_start', 't_end', 'timestamp']:
            if field in event and event[field]:
                try:
                    # Parse timestamp (handle both ISO format with/without Z)
                    old_ts_str = event[field].replace('Z', '+00:00') if 'Z' in event[field] else event[field]
                    old_ts = datetime.fromisoformat(old_ts_str)
                    
                    # Add delta
                    new_ts = old_ts + delta
                    
                    # Save in ISO format
                    event[field] = new_ts.isoformat()
                    rebased_count += 1
                except Exception as e:
                    print(f"⚠️  Warning: Could not parse {field}='{event[field]}': {e}")
    
    # Show new range
    new_times = [e.get('t_start') or e.get('timestamp') for e in events if e.get('t_start') or e.get('timestamp')]
    if new_times:
        print(f"Rebased range: {min(new_times)} → {max(new_times)}")
    
    print(f"\n✅ Rebased {rebased_count} timestamp fields across {len(events)} events")
    
    # Save
    with open(output_file, 'w') as f:
        for event in events:
            f.write(json.dumps(event) + '\n')
    
    print(f"✅ Saved to {output_file}")
    print("\n" + "=" * 80)
    print("Next step: Run scripts/update_weaviate_telemetry_events.py")
    print("=" * 80)

if __name__ == "__main__":
    main()

