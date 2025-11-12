#!/usr/bin/env python3
"""
Query real data from Weaviate and parquet to create realistic interaction flows.
This script gathers actual data that the agent would see during interactions.
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from elysia.util.client import ClientManager
from features.telemetry_vsm.src.worldstate_engine import WorldStateEngine
from weaviate.classes.query import Filter


async def query_alarms(client, asset_id="135_1570"):
    """Query actual alarms"""
    collection = client.collections.get("VSM_TelemetryEvent")
    results = await collection.query.fetch_objects(
        filters=Filter.by_property("asset_id").equal(asset_id) &
                Filter.by_property("severity").equal("critical"),
        limit=3
    )
    return [obj.properties for obj in results.objects]


async def query_vlog_cases(client, failure_mode="ingevroren_verdamper"):
    """Query actual vlog cases"""
    collection = client.collections.get("VSM_VlogCase")
    results = await collection.query.fetch_objects(
        filters=Filter.by_property("failure_mode").equal(failure_mode),
        limit=1
    )
    return [obj.properties for obj in results.objects]


async def query_manual_sections(client, smido_step="3P_procesinstellingen"):
    """Query actual manual sections"""
    collection = client.collections.get("VSM_ManualSections")
    results = await collection.query.fetch_objects(
        filters=Filter.by_property("smido_step").equal(smido_step) &
                Filter.by_property("content_type").not_equal("opgave"),
        limit=2
    )
    return [obj.properties for obj in results.objects]


async def query_patterns(client, query_text="room temp high suction extreme"):
    """Query actual patterns"""
    collection = client.collections.get("VSM_WorldStateSnapshot")
    results = await collection.query.near_text(
        query=query_text,
        limit=3
    )
    return [obj.properties for obj in results.objects]


def compute_worldstate_sample(asset_id="135_1570", timestamp_str="2024-07-21T14:03:00"):
    """Compute actual WorldState"""
    engine = WorldStateEngine("features/telemetry/timeseries_freezerdata/135_1570_cleaned_with_flags.parquet")
    timestamp = datetime.fromisoformat(timestamp_str)
    worldstate = engine.compute_worldstate(asset_id, timestamp, window_minutes=60)
    return worldstate


async def main():
    """Gather all real data"""
    print("=" * 70)
    print("Gathering Real Data for Interaction Flows")
    print("=" * 70)
    
    cm = ClientManager()
    
    try:
        async with cm.connect_to_async_client() as client:
            # 1. Alarms
            print("\n1. Querying Alarms...")
            alarms = await query_alarms(client)
            print(f"   Found {len(alarms)} critical alarm(s)")
            if alarms:
                alarm = alarms[0]
                print(f"   Sample: {alarm.get('event_id')} - {alarm.get('failure_mode')}")
                print(f"   Description: {alarm.get('description_nl', '')[:80]}...")
            
            # 2. Vlog Cases
            print("\n2. Querying Vlog Cases (frozen evaporator)...")
            cases = await query_vlog_cases(client, "ingevroren_verdamper")
            print(f"   Found {len(cases)} case(s)")
            if cases:
                case = cases[0]
                print(f"   Case ID: {case.get('case_id')}")
                print(f"   Problem: {case.get('problem_summary', '')[:80]}...")
                print(f"   Root Cause: {case.get('root_cause', '')[:80]}...")
            
            # 3. Manual Sections
            print("\n3. Querying Manual Sections (P2)...")
            manuals = await query_manual_sections(client, "3P_procesinstellingen")
            print(f"   Found {len(manuals)} section(s)")
            if manuals:
                manual = manuals[0]
                print(f"   Title: {manual.get('title', 'N/A')[:60]}...")
                print(f"   Content preview: {manual.get('content', '')[:100]}...")
            
            # 4. Patterns
            print("\n4. Querying Patterns...")
            patterns = await query_patterns(client, "room temp high suction extreme")
            print(f"   Found {len(patterns)} pattern(s)")
            if patterns:
                pattern = patterns[0]
                print(f"   Snapshot ID: {pattern.get('snapshot_id')}")
                print(f"   Failure Mode: {pattern.get('failure_mode')}")
                print(f"   Pattern: {pattern.get('typical_pattern', '')[:80]}...")
            
            # 5. WorldState
            print("\n5. Computing WorldState...")
            worldstate = compute_worldstate_sample("135_1570", "2024-07-21T14:03:00")
            print(f"   Current room temp: {worldstate['current_state'].get('current_room_temp')}°C")
            print(f"   Flags: {[k for k, v in worldstate.get('flags', {}).items() if v]}")
            print(f"   Health score: {worldstate.get('health_scores', {}).get('overall_health', 'N/A')}")
            
            # Save to JSON for reference
            output = {
                "alarms": alarms[:1] if alarms else [],
                "vlog_cases": cases[:1] if cases else [],
                "manual_sections": [{
                    "title": m.get("title"),
                    "content_preview": m.get("content", "")[:200]
                } for m in manuals[:1]] if manuals else [],
                "patterns": patterns[:1] if patterns else [],
                "worldstate_sample": {
                    "current_state": worldstate.get("current_state"),
                    "flags": {k: v for k, v in worldstate.get("flags", {}).items() if v},
                    "health_scores": worldstate.get("health_scores", {})
                }
            }
            
            output_path = Path("scripts/real_data_sample.json")
            with open(output_path, "w") as f:
                json.dump(output, f, indent=2, default=str)
            print(f"\n✅ Data saved to {output_path}")
            
    finally:
        await cm.close_clients()


if __name__ == "__main__":
    asyncio.run(main())

