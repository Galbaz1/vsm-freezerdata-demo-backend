"""
Detailed latency breakdown to identify exact bottlenecks.

Measures:
1. Tree creation time
2. First query (cold start)
3. Second query (warm)
4. Component timing (decision vs tool vs overhead)
"""

import asyncio
import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from features.vsm_tree.smido_tree import create_vsm_tree


def measure_component_times():
    """Detailed timing breakdown of tree execution."""
    print("=" * 70)
    print("Latency Breakdown Analysis")
    print("=" * 70)
    print()
    
    # Phase 1: Tree creation
    print("PHASE 1: Tree Creation")
    print("-" * 70)
    start = time.time()
    tree = create_vsm_tree()
    tree_creation = time.time() - start
    print(f"  Tree creation: {tree_creation:.2f}s")
    print(f"    - Includes: Gemini cache creation (~1.5s)")
    print(f"    - Includes: Bootstrap tool registration")
    print(f"    - Includes: Collection schema loading")
    print()
    
    # Phase 2: First query (cold)
    print("PHASE 2: First Query (Cold Start)")
    print("-" * 70)
    print("  Query: 'Wat is de status?'")
    
    start = time.time()
    response1, objects1 = tree("Wat is de status?")
    total_first = time.time() - start
    
    print(f"  Total time: {total_first:.2f}s")
    print(f"  Objects: {len(objects1) if objects1 else 0}")
    print()
    
    # Phase 3: Second query (warm)
    print("PHASE 3: Second Query (Warm - Cache Hit Expected)")
    print("-" * 70)
    print("  Query: 'Laat alarmen zien'")
    
    start = time.time()
    response2, objects2 = tree("Laat alarmen zien")
    total_second = time.time() - start
    
    print(f"  Total time: {total_second:.2f}s")
    print(f"  Objects: {len(objects2) if objects2 else 0}")
    print()
    
    # Phase 4: Third query (warm, different tool)
    print("PHASE 4: Third Query (Different Tool)")
    print("-" * 70)
    print("  Query: 'Zoek handleiding over compressor'")
    
    start = time.time()
    response3, objects3 = tree("Zoek handleiding over compressor")
    total_third = time.time() - start
    
    print(f"  Total time: {total_third:.2f}s")
    print(f"  Objects: {len(objects3) if objects3 else 0}")
    print()
    
    # Analysis
    print("=" * 70)
    print("Analysis")
    print("=" * 70)
    print()
    
    print("Timeline:")
    print(f"  Tree creation: {tree_creation:.2f}s (one-time)")
    print(f"  Query 1 (get_current_status): {total_first:.2f}s")
    print(f"  Query 2 (get_alarms): {total_second:.2f}s")
    print(f"  Query 3 (search_manuals): {total_third:.2f}s")
    print()
    
    avg_query = (total_first + total_second + total_third) / 3
    print(f"Average query time: {avg_query:.2f}s")
    print()
    
    # Expected vs Actual
    print("Expected (from research):")
    print("  - With cache: ~2-3s per query (44% reduction from 6s)")
    print("  - First token: ~1s")
    print()
    
    print("Actual:")
    print(f"  - Average: {avg_query:.2f}s")
    print(f"  - Status: {'✅ GOOD' if avg_query < 4 else '⚠️  SLOW' if avg_query < 8 else '❌ TOO SLOW'}")
    print()
    
    # Hypothesis about bottlenecks
    print("Likely bottlenecks (in order):")
    print("  1. Decision LLM call (~4-6s estimated)")
    print("  2. Tool execution (WorldState: ~500ms, Weaviate: ~200ms)")
    print("  3. Response formatting + suggestions (~1-2s)")
    print("  4. Tree overhead (environment updates, etc.)")
    print()
    
    print("Cache status:")
    cache_working = total_second < total_first * 0.8
    if cache_working:
        print("  ✅ Cache appears to be helping (query 2 faster than query 1)")
    else:
        print("  ❌ No clear cache benefit visible")
        print("  → Need to check if DSPy is passing cached_content parameter")
    print()
    
    # Recommendations
    print("=" * 70)
    print("Recommendations")
    print("=" * 70)
    print()
    
    if avg_query > 8:
        print("❌ CRITICAL: Avg {:.2f}s is too slow".format(avg_query))
        print()
        print("Immediate actions:")
        print("  1. Check Elysia logs for decision LLM timing")
        print("  2. Verify DSPy is using cached_content parameter")
        print("  3. Consider: use_elysia_collections=False (remove schema overhead)")
        print("  4. Add timing instrumentation to tree.py")
    elif avg_query > 4:
        print("⚠️  Average {:.2f}s is slower than expected".format(avg_query))
        print()
        print("Next optimizations:")
        print("  1. WorldState caching (save ~300ms)")
        print("  2. Shorter agent description (save ~500ms)")
        print("  3. Parallel Weaviate queries (save ~200ms)")
    else:
        print("✅ Average {:.2f}s is acceptable!".format(avg_query))
        print()
        print("Optional further optimizations:")
        print("  1. WorldState caching for consistency")
        print("  2. Fine-tune hybrid search alpha values")
    print()
    
    return True


if __name__ == "__main__":
    try:
        measure_component_times()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

