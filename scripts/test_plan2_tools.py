#!/usr/bin/env python3
"""
Test script for Plan 2 tools (GetAlarms, QueryTelemetryEvents, QueryVlogCases)
Tests the tools through their __call__ method with proper Elysia arguments.
"""

import asyncio
import sys
from elysia import Tree, Settings
from elysia.api.custom_tools import get_alarms, query_telemetry_events, query_vlog_cases
from elysia.util.client import ClientManager


async def test_get_alarms():
    """Test 1: GetAlarms tool"""
    print("\n=== Test 1: GetAlarms ===")
    
    try:
        # Create a Tree instance to get proper TreeData and LMs
        tree = Tree(
            branch_initialisation="empty",
            low_memory=True,  # Don't load models for testing
            settings=Settings.from_smart_setup()
        )
        
        cm = ClientManager()
        results = []
        
        # Call tool through __call__ with proper arguments
        async for result in get_alarms.__call__(
            tree_data=tree.tree_data,
            inputs={"asset_id": "135_1570", "severity": "critical"},
            base_lm=None,  # Not needed for low_memory
            complex_lm=None,  # Not needed for low_memory
            client_manager=cm
        ):
            results.append(result)
        
        # Check for Result objects
        result_objects = [r for r in results if hasattr(r, 'objects')]
        if result_objects:
            print(f"✅ GetAlarms: Found {len(result_objects[0].objects)} alarm(s)")
            return True
        else:
            print(f"❌ GetAlarms: No Result objects found. Results: {results}")
            return False
    except Exception as e:
        print(f"❌ GetAlarms: Error - {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up connections
        if 'cm' in locals():
            try:
                async with cm.connect_to_async_client() as client:
                    pass  # Connection will close automatically
            except:
                pass


async def test_query_telemetry_events():
    """Test 2: QueryTelemetryEvents with frozen evaporator"""
    print("\n=== Test 2: QueryTelemetryEvents ===")
    
    try:
        # Create a Tree instance to get proper TreeData and LMs
        tree = Tree(
            branch_initialisation="empty",
            low_memory=True,  # Don't load models for testing
            settings=Settings.from_smart_setup()
        )
        
        cm = ClientManager()
        results = []
        
        # Call tool through __call__ with proper arguments
        async for result in query_telemetry_events.__call__(
            tree_data=tree.tree_data,
            inputs={"failure_mode": "ingevroren_verdamper", "limit": 3},
            base_lm=None,  # Not needed for low_memory
            complex_lm=None,  # Not needed for low_memory
            client_manager=cm
        ):
            results.append(result)
        
        # Check for Result objects
        result_objects = [r for r in results if hasattr(r, 'objects')]
        if result_objects:
            print(f"✅ QueryTelemetryEvents: Found {len(result_objects[0].objects)} event(s)")
            return True
        else:
            print(f"❌ QueryTelemetryEvents: No Result objects found. Results: {results}")
            return False
    except Exception as e:
        print(f"❌ QueryTelemetryEvents: Error - {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up connections
        if 'cm' in locals():
            try:
                async with cm.connect_to_async_client() as client:
                    pass  # Connection will close automatically
            except:
                pass


async def test_query_vlog_cases():
    """Test 3: QueryVlogCases for A3"""
    print("\n=== Test 3: QueryVlogCases ===")
    
    try:
        # Create a Tree instance to get proper TreeData and LMs
        tree = Tree(
            branch_initialisation="empty",
            low_memory=True,  # Don't load models for testing
            settings=Settings.from_smart_setup()
        )
        
        cm = ClientManager()
        results = []
        
        # Call tool through __call__ with proper arguments
        async for result in query_vlog_cases.__call__(
            tree_data=tree.tree_data,
            inputs={
                "problem_description": "verdamper bevroren",
                "failure_mode": "ingevroren_verdamper"
            },
            base_lm=None,  # Not needed for low_memory
            complex_lm=None,  # Not needed for low_memory
            client_manager=cm
        ):
            results.append(result)
        
        # Check for Result objects
        result_objects = [r for r in results if hasattr(r, 'objects')]
        if result_objects:
            print(f"✅ QueryVlogCases: Found {len(result_objects[0].objects)} case(s)")
            if result_objects[0].objects:
                case = result_objects[0].objects[0]
                case_id = case.get('case_id', 'N/A')
                print(f"   First case: {case_id} - {case.get('problem_summary', 'N/A')[:50]}...")
                # Check if A3 case is found (preferred) or any case with frozen evaporator
                if case_id == "A3" or "ingevroren" in str(case.get('problem_summary', '')).lower():
                    print(f"   ✅ Found frozen evaporator case: {case_id}")
            return True
        else:
            print(f"❌ QueryVlogCases: No Result objects found. Results: {results}")
            return False
    except Exception as e:
        print(f"❌ QueryVlogCases: Error - {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up connections
        if 'cm' in locals():
            try:
                async with cm.connect_to_async_client() as client:
                    pass  # Connection will close automatically
            except:
                pass


async def main():
    """Run all tests"""
    print("Testing Plan 2 Tools (Simple Query Tools)")
    print("=" * 50)
    
    results = []
    results.append(await test_get_alarms())
    results.append(await test_query_telemetry_events())
    results.append(await test_query_vlog_cases())
    
    print("\n" + "=" * 50)
    print("Summary:")
    print(f"  GetAlarms: {'✅ PASS' if results[0] else '❌ FAIL'}")
    print(f"  QueryTelemetryEvents: {'✅ PASS' if results[1] else '❌ FAIL'}")
    print(f"  QueryVlogCases: {'✅ PASS' if results[2] else '❌ FAIL'}")
    
    if all(results):
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

