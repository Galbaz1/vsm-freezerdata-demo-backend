#!/usr/bin/env python3
"""
Rebase telemetry timestamps to make data appear current through 2026-01-01.

Current range: 2022-10-20 16:02:00 to 2024-04-01 01:59:00
Target range: Should end at 2026-01-01 00:00:00 (or 23:59:00)

Shift calculation:
- Current end: 2024-04-01 01:59:00
- Target end: 2026-01-01 00:00:00
- Shift: ~640 days forward
"""
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import shutil

# Configuration
CURRENT_END = datetime(2024, 4, 1, 1, 59, 0)
TARGET_END = datetime(2026, 1, 1, 0, 0, 0)
# Calculate exact shift to reach target end date
SHIFT_DELTA = TARGET_END - CURRENT_END
SHIFT_DAYS = SHIFT_DELTA.days

print(f"Telemetry Rebase Configuration:")
print(f"  Current end: {CURRENT_END}")
print(f"  Target end: {TARGET_END}")
print(f"  Shift: {SHIFT_DAYS} days ({SHIFT_DELTA})")
print(f"  New start: {datetime(2022, 10, 20, 16, 2, 0) + SHIFT_DELTA}")
print(f"  New end: {CURRENT_END + SHIFT_DELTA}")
print()

# Parquet files to process
PARQUET_FILES = [
    "features/telemetry/timeseries_freezerdata/135_1570_cleaned.parquet",
    "features/telemetry/timeseries_freezerdata/135_1570_cleaned_with_flags.parquet",
]

def backup_file(filepath: Path):
    """Create backup of original file"""
    backup_path = filepath.with_suffix(filepath.suffix + '.backup')
    if not backup_path.exists():
        print(f"Creating backup: {backup_path}")
        shutil.copy2(filepath, backup_path)
    else:
        print(f"Backup already exists: {backup_path}")

def rebase_parquet(filepath: Path, shift_delta: timedelta):
    """Rebase timestamps in parquet file"""
    print(f"\nProcessing: {filepath}")
    
    # Load parquet
    df = pd.read_parquet(filepath)
    original_min = df.index.min()
    original_max = df.index.max()
    original_rows = len(df)
    
    print(f"  Original range: {original_min} to {original_max}")
    print(f"  Original rows: {original_rows:,}")
    
    # Shift index
    df.index = df.index + shift_delta
    
    new_min = df.index.min()
    new_max = df.index.max()
    new_rows = len(df)
    
    print(f"  New range: {new_min} to {new_max}")
    print(f"  New rows: {new_rows:,}")
    
    # Validate
    if original_rows != new_rows:
        raise ValueError(f"Row count mismatch: {original_rows} != {new_rows}")
    
    # Backup original
    backup_file(filepath)
    
    # Write rebased file
    print(f"  Writing rebased file...")
    df.to_parquet(filepath, engine='pyarrow')
    
    print(f"  ✓ Successfully rebased {filepath}")
    
    return {
        'original_min': original_min,
        'original_max': original_max,
        'new_min': new_min,
        'new_max': new_max,
        'rows': new_rows
    }

def main():
    results = []
    
    for parquet_file in PARQUET_FILES:
        filepath = Path(parquet_file)
        if not filepath.exists():
            print(f"⚠ Warning: File not found: {filepath}")
            continue
        
        try:
            result = rebase_parquet(filepath, SHIFT_DELTA)
            results.append((filepath, result))
        except Exception as e:
            print(f"✗ Error processing {filepath}: {e}")
            raise
    
    # Summary
    print("\n" + "="*80)
    print("REBASE SUMMARY")
    print("="*80)
    for filepath, result in results:
        print(f"\n{filepath.name}:")
        print(f"  Original: {result['original_min']} to {result['original_max']}")
        print(f"  New:      {result['new_min']} to {result['new_max']}")
        print(f"  Rows:     {result['rows']:,}")
    
    print(f"\n✓ Rebase complete! Original files backed up with .backup extension")
    print(f"\nNext steps:")
    print(f"  1. Regenerate telemetry events: python3 features/telemetry_vsm/src/detect_events.py")
    print(f"  2. Update code references to new date range")
    print(f"  3. Re-import events to Weaviate if needed")

if __name__ == "__main__":
    main()

