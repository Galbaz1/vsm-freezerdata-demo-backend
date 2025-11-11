#!/usr/bin/env python3
"""
Test script for Plan 4 tools (GetAssetHealth, AnalyzeSensorPattern)
Tests the tools through their __call__ method with proper Elysia arguments.
"""

import asyncio
import sys
import warnings
from datetime import datetime
from elysia import Tree, Settings
from elysia.api.custom_tools import get_asset_health, analyze_sensor_pattern
from elysia.util.client import ClientManager

# Suppress ResourceWarnings for cleaner test output
warnings.filterwarnings("ignore", category=ResourceWarning)


async def test_get_asset_health(client_manager=None):
    """Test 1: GetAssetHealth W vs C comparison"""
    print("\n=== Test 1: GetAssetHealth (W vs C) ===")
    
    try:
        # Create a Tree instance to get proper TreeData and LMs
        tree = Tree(
            branch_initialisation="empty",
            low_memory=True,  # Don't load models for testing
            settings=Settings.from_smart_setup()
        )
        
        cm = client_manager or ClientManager()
        results = []
        
        # Test with known out-of-balance timestamp (frozen evaporator scenario)
        # Use a timestamp from the telemetry data
        async for result in get_asset_health.__call__(
            tree_data=tree.tree_data,
            inputs={
                "asset_id": "135_1570",
                "timestamp": "2024-01-01T12:00:00",
                "window_minutes": 60
            },
            base_lm=None,  # Not needed for low_memory
            complex_lm=None,  # Not needed for low_memory
            client_manager=cm
        ):
            results.append(result)
        
        # Check for Result objects
        result_objects = [r for r in results if hasattr(r, 'objects')]
        if not result_objects:
            print("❌ GetAssetHealth: No Result objects found")
            return False
        
        health = result_objects[0].objects[0]
        
        # Verify structure
        assert 'overall_health' in health, "Missing overall_health field"
        assert 'out_of_balance_factors' in health, "Missing out_of_balance_factors field"
        assert 'worldstate_summary' in health, "Missing worldstate_summary field"
        assert 'recommendations' in health, "Missing recommendations field"
        
        print(f"✅ GetAssetHealth: Health status = {health['overall_health']}")
        print(f"   Out of balance factors: {len(health['out_of_balance_factors'])}")
        print(f"   Recommendations: {len(health['recommendations'])}")
        
        if health['out_of_balance_factors']:
            print("   Factors:")
            for factor in health['out_of_balance_factors']:
                print(f"     - {factor['factor']}: {factor.get('current')} vs {factor.get('design', factor.get('design_range', 'N/A'))}")
        
        return True
        
    except Exception as e:
        print(f"❌ GetAssetHealth: Error - {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_analyze_sensor_pattern(client_manager=None):
    """Test 2: AnalyzeSensorPattern - match frozen evaporator pattern"""
    print("\n=== Test 2: AnalyzeSensorPattern ===")
    
    try:
        # Create a Tree instance to get proper TreeData and LMs
        tree = Tree(
            branch_initialisation="empty",
            low_memory=True,  # Don't load models for testing
            settings=Settings.from_smart_setup()
        )
        
        cm = client_manager or ClientManager()
        results = []
        
        # Test with frozen evaporator scenario timestamp
        async for result in analyze_sensor_pattern.__call__(
            tree_data=tree.tree_data,
            inputs={
                "asset_id": "135_1570",
                "timestamp": "2024-01-01T12:00:00",
                "window_minutes": 60
            },
            base_lm=None,  # Not needed for low_memory
            complex_lm=None,  # Not needed for low_memory
            client_manager=cm
        ):
            results.append(result)
        
        # Check for Result objects
        result_objects = [r for r in results if hasattr(r, 'objects')]
        if not result_objects:
            print("❌ AnalyzeSensorPattern: No Result objects found")
            return False
        
        analysis = result_objects[0].objects[0]
        
        # Verify structure
        assert 'current_worldstate' in analysis, "Missing current_worldstate field"
        assert 'matched_patterns' in analysis, "Missing matched_patterns field"
        assert 'detected_failure_mode' in analysis, "Missing detected_failure_mode field"
        assert 'is_uit_balans' in analysis, "Missing is_uit_balans field"
        
        print(f"✅ AnalyzeSensorPattern: Found {len(analysis['matched_patterns'])} pattern(s)")
        print(f"   Detected failure mode: {analysis['detected_failure_mode']}")
        print(f"   Is uit balans: {analysis['is_uit_balans']}")
        
        if analysis['matched_patterns']:
            print("   Matched patterns:")
            for i, pattern in enumerate(analysis['matched_patterns'][:3], 1):
                print(f"     {i}. {pattern['snapshot_id']} - {pattern['failure_mode']}")
                print(f"        Type: {pattern.get('uit_balans_type', 'N/A')}")
                print(f"        Balance factors: {len(pattern.get('balance_factors', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ AnalyzeSensorPattern: Error - {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_balance_detection(client_manager=None):
    """Test 3: Verify balance detection works"""
    print("\n=== Test 3: Balance Detection Verification ===")
    
    try:
        tree = Tree(
            branch_initialisation="empty",
            low_memory=True,
            settings=Settings.from_smart_setup()
        )
        
        cm = client_manager or ClientManager()
        
        # Test GetAssetHealth
        health_results = []
        async for result in get_asset_health.__call__(
            tree_data=tree.tree_data,
            inputs={"asset_id": "135_1570", "timestamp": "2024-01-01T12:00:00"},
            base_lm=None,
            complex_lm=None,
            client_manager=cm
        ):
            health_results.append(result)
        
        health_obj = [r for r in health_results if hasattr(r, 'objects')]
        if health_obj:
            health = health_obj[0].objects[0]
            print(f"✅ Balance check completed")
            print(f"   Overall health: {health['overall_health']}")
            print(f"   Factors checked: {health_obj[0].metadata.get('factors_checked', 'N/A')}")
        
        # Test AnalyzeSensorPattern
        pattern_results = []
        async for result in analyze_sensor_pattern.__call__(
            tree_data=tree.tree_data,
            inputs={"asset_id": "135_1570", "timestamp": "2024-01-01T12:00:00"},
            base_lm=None,
            complex_lm=None,
            client_manager=cm
        ):
            pattern_results.append(result)
        
        pattern_obj = [r for r in pattern_results if hasattr(r, 'objects')]
        if pattern_obj:
            analysis = pattern_obj[0].objects[0]
            print(f"✅ Pattern matching completed")
            print(f"   Patterns checked: {pattern_obj[0].metadata.get('patterns_checked', 'N/A')}")
            print(f"   Best match: {pattern_obj[0].metadata.get('best_match', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Balance Detection: Error - {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Plan 4 Tools Test Suite")
    print("=" * 60)
    
    # Create a single ClientManager for all tests to share
    client_manager = ClientManager()
    
    try:
        tests = [
            ("GetAssetHealth", test_get_asset_health),
            ("AnalyzeSensorPattern", test_analyze_sensor_pattern),
            ("Balance Detection", test_balance_detection)
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = await test_func(client_manager)
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name}: Unexpected error - {str(e)}")
                results.append((test_name, False))
        
        # Summary
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {test_name}")
        
        print(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 All Plan 4 tests passed!")
            return 0
        else:
            print(f"\n⚠️  {total - passed} test(s) failed")
            return 1
    finally:
        # Ensure clients are properly closed
        try:
            await client_manager.close_clients()
        except Exception as e:
            # Ignore errors during cleanup
            pass


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

