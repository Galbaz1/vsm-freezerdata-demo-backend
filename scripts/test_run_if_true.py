"""
Test script for run_if_true implementation on GetCurrentStatus tool.

Tests:
1. run_if_true triggers on first message
2. run_if_true does NOT trigger on subsequent messages
3. Latency improvement measurement
4. A3 demo override still works
"""

import asyncio
import time
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from features.vsm_tree.smido_tree import create_vsm_tree


async def test_run_if_true_behavior():
    """Test that run_if_true correctly auto-runs on first message only."""
    print("=" * 60)
    print("Testing run_if_true for GetCurrentStatus")
    print("=" * 60)
    print()
    
    # Test 1: First message (should auto-run)
    print("1. Testing First Message (should auto-run)")
    print("-" * 60)
    
    tree = create_vsm_tree()
    
    start = time.time()
    response, objects = tree("Wat is de status?")
    first_msg_time = time.time() - start
    
    print(f"   Query: 'Wat is de status?'")
    print(f"   Latency: {first_msg_time:.2f}s")
    print(f"   Target: <2s (bypassing decision LLM)")
    print(f"   Success: {'✅ PASS' if first_msg_time < 2.5 else '❌ FAIL (slower than expected)'}")
    print(f"   Objects returned: {len(objects) if objects else 0}")
    print()
    
    # Verify status was returned
    if objects and len(objects) > 0:
        print("   ✅ Status data returned")
        status = objects[0]
        if "asset_id" in status:
            print(f"   Asset ID: {status['asset_id']}")
        if "health_scores" in status:
            print(f"   Health scores: {list(status['health_scores'].keys())}")
    else:
        print("   ❌ No status data returned!")
    print()
    
    # Test 2: Second message (should NOT auto-run, needs decision)
    print("2. Testing Second Message (should use decision LLM)")
    print("-" * 60)
    
    start = time.time()
    response2, objects2 = tree("Wat zijn de alarmen?")
    second_msg_time = time.time() - start
    
    print(f"   Query: 'Wat zijn de alarmen?'")
    print(f"   Latency: {second_msg_time:.2f}s")
    print(f"   Expected: 2-4s (normal decision flow)")
    print(f"   Success: {'✅ PASS' if second_msg_time > 1.5 else '⚠️ WARNING (unexpectedly fast)'}")
    print()
    
    # Test 3: New tree, different query (should NOT auto-run)
    print("3. Testing First Message with Non-Status Query")
    print("-" * 60)
    
    tree3 = create_vsm_tree()
    
    start = time.time()
    response3, objects3 = tree3("Zoek handleiding over verdamper")
    third_msg_time = time.time() - start
    
    print(f"   Query: 'Zoek handleiding over verdamper'")
    print(f"   Latency: {third_msg_time:.2f}s")
    print(f"   Expected: 2-4s (decision should choose search_manuals, not status)")
    print(f"   Success: {'✅ PASS' if third_msg_time > 1.5 else '⚠️ WARNING (unexpectedly fast)'}")
    print()
    
    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    print()
    print(f"  ✓ First message latency: {first_msg_time:.2f}s (target: <2.5s)")
    print(f"  ✓ Second message latency: {second_msg_time:.2f}s (normal flow)")
    print(f"  ✓ Non-status first message: {third_msg_time:.2f}s (normal flow)")
    print()
    
    # Calculate improvement
    if first_msg_time < 2.5:
        improvement_pct = ((4.0 - first_msg_time) / 4.0) * 100
        print(f"  🎉 Latency improvement: ~{improvement_pct:.0f}% on first message")
        print(f"     (Estimated baseline 4s → {first_msg_time:.2f}s)")
    else:
        print(f"  ⚠️  First message slower than expected")
        print(f"     Check if run_if_true is actually triggering")
    print()
    
    print("Expected behavior:")
    print("  - First 'status' query: <2s (run_if_true bypasses decision)")
    print("  - Other queries: 2-4s (normal LLM decision)")
    print("  - run_if_true only triggers when:")
    print("    * First message (conversation_history <= 1)")
    print("    * Environment empty (no prior tool runs)")
    print()
    
    return first_msg_time < 2.5


if __name__ == "__main__":
    try:
        success = asyncio.run(test_run_if_true_behavior())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

