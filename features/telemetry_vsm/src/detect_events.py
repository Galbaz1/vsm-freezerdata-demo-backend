#!/usr/bin/env python3
"""
Detect telemetry events ("uit balans" incidents) from parquet data.
Computes WorldState features and classifies failure modes.
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict

# Parquet file
PARQUET_FILE = "features/telemetry/timeseries_freezerdata/135_1570_cleaned_with_flags.parquet"
ASSET_ID = "135_1570"

# Design parameters (from commissioning data)
TARGET_TEMP = -33.0
TEMP_WARNING_THRESHOLD = -18.0
TEMP_CRITICAL_THRESHOLD = -10.0


def load_telemetry() -> pd.DataFrame:
    """Load telemetry parquet file"""
    print("Loading telemetry data...")
    df = pd.read_parquet(PARQUET_FILE)
    print(f"Loaded {len(df):,} rows")
    print(f"Date range: {df.index[0]} to {df.index[-1]}")
    print(f"Columns: {list(df.columns)}")
    return df


def detect_event_periods(df: pd.DataFrame) -> List[Dict]:
    """Detect continuous periods where system is 'uit balans'"""
    events = []
    
    # Define event conditions
    df['is_event'] = (
        (df['_flag_main_temp_high'] == True) |
        (df['_flag_hot_gas_low'] == True) |
        (df['_flag_liquid_extreme'] == True) |
        (df['_flag_suction_extreme'] == True) |
        (df['_flag_ambient_extreme'] == True) |
        (df['sGekoeldeRuimte'] > TEMP_WARNING_THRESHOLD)
    )
    
    # Find continuous event periods
    df['event_group'] = (df['is_event'] != df['is_event'].shift()).cumsum()
    
    # Group by event periods
    for event_id, group in df[df['is_event']].groupby('event_group'):
        if len(group) < 30:  # Skip events <30 minutes
            continue
        
        event = {
            "event_id": f"evt_{group.index[0].strftime('%Y%m%d_%H%M')}",
            "asset_id": ASSET_ID,
            "t_start": group.index[0].isoformat(),
            "t_end": group.index[-1].isoformat(),
            "duration_minutes": int((group.index[-1] - group.index[0]).total_seconds() / 60),
            
            # WorldState aggregates
            "room_temp_min": float(group['sGekoeldeRuimte'].min()),
            "room_temp_max": float(group['sGekoeldeRuimte'].max()),
            "room_temp_mean": float(group['sGekoeldeRuimte'].mean()),
            "hot_gas_mean": float(group['sHeetgasLeiding'].mean()),
            "suction_mean": float(group['sZuigleiding'].mean()),
            "liquid_mean": float(group['sVloeistofleiding'].mean()),
            "ambient_mean": float(group['sOmgeving'].mean()),
            
            # Trends
            "room_temp_trend": float((group['sGekoeldeRuimte'].iloc[-1] - group['sGekoeldeRuimte'].iloc[0]) / 
                                    (len(group) / 60)) if len(group) > 1 else 0.0,
            
            # Door activity
            "door_open_ratio": float(group['sDeurcontact'].mean()),
            
            # Flags (which were active)
            "flags_active": {
                "main_temp_high": bool(group['_flag_main_temp_high'].any()),
                "hot_gas_low": bool(group['_flag_hot_gas_low'].any()),
                "liquid_extreme": bool(group['_flag_liquid_extreme'].any()),
                "suction_extreme": bool(group['_flag_suction_extreme'].any()),
                "ambient_extreme": bool(group['_flag_ambient_extreme'].any())
            },
            
            # Reference
            "parquet_path": PARQUET_FILE,
            "time_range_start": group.index[0].isoformat(),
            "time_range_end": group.index[-1].isoformat()
        }
        
        events.append(event)
    
    return events


def classify_event(event: Dict) -> Dict:
    """Classify event failure mode and generate descriptions (pattern-based)"""
    flags = event["flags_active"]
    room_temp = event["room_temp_mean"]
    hot_gas = event["hot_gas_mean"]
    trend = event["room_temp_trend"]
    
    failure_modes = []
    components = []
    description_parts = []
    
    # Determine failure modes based on flags and values
    if flags["main_temp_high"]:
        failure_modes.append("te_hoge_temperatuur")
        description_parts.append(f"Temperatuur te hoog ({room_temp:.1f}°C)")
    
    if flags["suction_extreme"] and flags["main_temp_high"]:
        failure_modes.append("ingevroren_verdamper")
        components.extend(["verdamper", "ontdooiheater"])
        description_parts.append("Verdamper mogelijk bevroren")
    
    if flags["hot_gas_low"]:
        failure_modes.append("compressor_draait_niet")
        components.append("compressor")
        description_parts.append(f"Heetgas laag ({hot_gas:.1f}°C)")
    
    if flags["liquid_extreme"]:
        failure_modes.append("expansieventiel_defect")
        components.extend(["expansieventiel", "filter_droger"])
        description_parts.append("Vloeistofleiding extreem")
    
    if flags["ambient_extreme"]:
        failure_modes.append("koelproces_uit_balans")
        components.append("condensor")
        description_parts.append("Omgevingstemperatuur extreem")
    
    if event["door_open_ratio"] > 0.3:
        failure_modes.append("deur_probleem")
        components.append("deur")
        description_parts.append(f"Deur vaak open ({event['door_open_ratio']*100:.0f}%)")
    
    # Severity
    if room_temp > TEMP_CRITICAL_THRESHOLD:
        severity = "critical"
    elif room_temp > TEMP_WARNING_THRESHOLD:
        severity = "warning"
    else:
        severity = "info"
    
    # Generate description
    trend_text = "stijgend" if trend > 0.5 else "dalend" if trend < -0.5 else "stabiel"
    description_nl = f"Storing gedetecteerd: {'. '.join(description_parts)}. " if description_parts else "Afwijking gedetecteerd. "
    description_nl += f"Temperatuur trend: {trend_text} ({trend:.1f}°C/uur). "
    description_nl += f"Duur: {event['duration_minutes']} minuten."
    
    # WorldState summary
    active_flags = [k for k, v in flags.items() if v]
    worldstate_summary = f"Flags: {', '.join(active_flags) if active_flags else 'none'}. "
    worldstate_summary += f"Room: {room_temp:.1f}°C, HotGas: {hot_gas:.1f}°C, Trend: {trend:.1f}°C/hr"
    
    # Add classifications to event
    event["failure_modes"] = list(set(failure_modes)) if failure_modes else ["algemeen"]
    event["failure_mode"] = event["failure_modes"][0]
    event["affected_components"] = list(set(components)) if components else []
    event["severity"] = severity
    event["description_nl"] = description_nl
    event["worldstate_summary"] = worldstate_summary
    
    # Cross-references (empty for now, will be linked later)
    event["related_manual_sections"] = []
    event["related_vlog_cases"] = []
    event["related_diagrams"] = []
    
    # Remove flags_active dict (stored in worldstate_summary)
    del event["flags_active"]
    
    return event


def main():
    # Load data
    df = load_telemetry()
    
    # Detect events
    print("\nDetecting event periods...")
    events = detect_event_periods(df)
    print(f"Found {len(events)} events (duration >= 30 minutes)")
    
    # Classify events
    print("\nClassifying events...")
    for i, event in enumerate(events):
        events[i] = classify_event(event)
        if (i + 1) % 100 == 0:
            print(f"Classified {i + 1}/{len(events)} events...")
    
    # Save output
    output_path = "features/telemetry_vsm/output/telemetry_events.jsonl"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        for event in events:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    
    print(f"\nSaved {len(events)} events to {output_path}")
    
    # Statistics
    print(f"\n=== Statistics ===")
    print(f"Total events: {len(events)}")
    print(f"Severity breakdown:")
    severity_counts = {}
    for e in events:
        severity_counts[e["severity"]] = severity_counts.get(e["severity"], 0) + 1
    for sev, count in severity_counts.items():
        print(f"  {sev}: {count}")
    
    print(f"\nTop failure modes:")
    failure_counts = {}
    for e in events:
        for mode in e["failure_modes"]:
            failure_counts[mode] = failure_counts.get(mode, 0) + 1
    for mode, count in sorted(failure_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"  {mode}: {count}")
    
    print(f"\nAverage event duration: {sum(e['duration_minutes'] for e in events) / len(events):.1f} minutes")
    print(f"Longest event: {max(e['duration_minutes'] for e in events)} minutes")


if __name__ == "__main__":
    main()

