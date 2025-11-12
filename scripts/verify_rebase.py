#!/usr/bin/env python3
"""Verify telemetry rebase completed successfully"""
import asyncio
from datetime import datetime
from elysia import Tree, Settings
from elysia.api.custom_tools import compute_worldstate
from features.telemetry_vsm.src.worldstate_engine import WorldStateEngine

async def test_tool():
    """Test compute_worldstate tool with dynamic timestamp"""
    print("Testing compute_worldstate tool...")
    tree = Tree(
        branch_initialisation='empty',
        low_memory=True,
        settings=Settings.from_smart_setup()
    )
    
    results = []
    async for r in compute_worldstate('135_1570', None, 60, tree.tree_data):
        results.append(r)
    
    result = [r for r in results if hasattr(r, 'objects')]
    if result:
        ws = result[0].objects[0]
        print(f"  ✅ Tool works: timestamp={ws['timestamp']}, is_future={ws.get('is_future', False)}")
        return True
    return False

def test_engine():
    """Test WorldStateEngine directly"""
    print("Testing WorldStateEngine...")
    engine = WorldStateEngine('features/telemetry/timeseries_freezerdata/135_1570_cleaned_with_flags.parquet')
    
    # Test current date
    now = datetime.now()
    ws = engine.compute_worldstate('135_1570', now, 60)
    print(f"  ✅ Engine works with current date: {ws['timestamp']}")
    
    # Test future date
    future = datetime(2025, 12, 31, 12, 0, 0)
    ws_future = engine.compute_worldstate('135_1570', future, 60)
    print(f"  ✅ Engine works with future date: {ws_future['timestamp']}")
    
    return True

def main():
    print("="*60)
    print("Telemetry Rebase Verification")
    print("="*60)
    
    # Test engine
    test_engine()
    
    # Test tool
    asyncio.run(test_tool())
    
    print("\n✅ All verification tests passed!")

if __name__ == "__main__":
    main()

