"""
Test script for Gemini Context Caching implementation.

Tests:
1. Cache creation during tree initialization
2. Cache statistics retrieval
3. Cache refresh functionality
"""

import asyncio
import time
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from features.vsm_tree.smido_tree import create_vsm_tree


async def test_cache_creation():
    """Test cache creation and basic functionality."""
    print("=" * 60)
    print("Testing Gemini Context Caching")
    print("=" * 60)
    print()
    
    # Test 1: Create tree (should create cache)
    print("1. Creating VSM tree with context cache...")
    start = time.time()
    tree = create_vsm_tree()
    creation_time = time.time() - start
    print(f"   Tree created in {creation_time:.2f}s")
    print()
    
    # Test 2: Check cache
    if hasattr(tree, '_context_cache'):
        stats = tree._context_cache.get_cache_stats()
        print("2. Cache Statistics:")
        print(f"   Cache name: {stats['cache_name']}")
        print(f"   Created at: {stats['created_at']}")
        print(f"   TTL: {stats['ttl_seconds']}s ({stats['ttl_seconds']/3600:.1f} hours)")
        print(f"   Active: {stats['is_active']}")
        print()
    else:
        print("   ERROR: Cache not created!")
        return False
    
    # Test 3: Cache refresh
    print("3. Testing cache refresh...")
    cache_name_before = tree._context_cache.get_cache_name()
    
    refresh_start = time.time()
    new_cache_name = tree._context_cache.refresh_cache(tree)
    refresh_time = time.time() - refresh_start
    
    cache_name_after = tree._context_cache.get_cache_name()
    
    print(f"   Before: {cache_name_before}")
    print(f"   After:  {cache_name_after}")
    print(f"   Refreshed: {cache_name_before != cache_name_after}")
    print(f"   Refresh time: {refresh_time:.2f}s")
    print()
    
    # Test 4: Verify new cache stats
    if new_cache_name:
        new_stats = tree._context_cache.get_cache_stats()
        print("4. New Cache Statistics:")
        print(f"   Cache name: {new_stats['cache_name']}")
        print(f"   Created at: {new_stats['created_at']}")
        print(f"   Active: {new_stats['is_active']}")
        print()
    else:
        print("   WARNING: Cache refresh returned None")
        print()
    
    # Summary
    print("=" * 60)
    print("Test Complete")
    print("=" * 60)
    print()
    print("Summary:")
    print(f"  ✓ Cache creation: {'SUCCESS' if stats['is_active'] else 'FAILED'}")
    print(f"  ✓ Cache stats: {'SUCCESS' if stats['cache_name'] else 'FAILED'}")
    print(f"  ✓ Cache refresh: {'SUCCESS' if cache_name_before != cache_name_after else 'FAILED'}")
    print()
    print("Next steps:")
    print("  1. Run `elysia start` to test with actual queries")
    print("  2. Monitor logs for cache hit/miss info")
    print("  3. Test /cache/stats endpoint: GET http://localhost:8000/cache/stats")
    print("  4. Test /cache/refresh endpoint: POST http://localhost:8000/cache/refresh")
    print()
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_cache_creation())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

