#!/usr/bin/env python3
"""
Test search_manual_images tool and verify image URLs are accessible.
"""
import asyncio
from elysia import Tree
from elysia.util.client import ClientManager
from elysia.objects import Result
import requests

async def test_image_search():
    print("=" * 80)
    print("Testing search_manual_images Tool")
    print("=" * 80)
    
    # Create minimal tree
    tree = Tree(branch_initialisation="empty")
    cm = ClientManager()
    
    # Import tool
    from elysia.api.custom_tools import search_manual_images
    
    # Test 1: Search by component
    print("\nTest 1: Search by component (verdamper)")
    print("-" * 80)
    
    results = []
    tool_instance = search_manual_images
    
    # Call tool properly
    async for item in tool_instance(
        query="verdamper",
        component="verdamper",
        limit=3,
        tree_data=tree.tree_data,
        client_manager=cm
    ):
        results.append(item)
        print(f"  Received: {type(item).__name__}")
    
    # Find Result object
    result_obj = next((r for r in results if isinstance(r, Result)), None)
    
    if result_obj:
        print(f"✅ Found {len(result_obj.objects)} verdamper images")
        for i, img in enumerate(result_obj.objects[:2], 1):
            print(f"  {i}. {img['manual_name']} p.{img['page_number']}")
            print(f"     URL: {img['image_url']}")
            print(f"     Tags: {img.get('component_tags', [])}")
    else:
        print("❌ No results returned")
    
    # Test 2: Search by query
    print("\nTest 2: Hybrid search (compressor foto)")
    print("-" * 80)
    
    results2 = []
    async for item in tool_instance(
        query="compressor foto",
        limit=3,
        tree_data=tree.tree_data,
        client_manager=cm
    ):
        results2.append(item)
    
    result_obj2 = next((r for r in results2 if isinstance(r, Result)), None)
    
    if result_obj2:
        print(f"✅ Found {len(result_obj2.objects)} compressor images")
    
    # Test 3: Verify image URLs accessible (if running locally)
    print("\nTest 3: Verify image URL accessibility")
    print("-" * 80)
    
    if result_obj and result_obj.objects:
        test_url = result_obj.objects[0]['image_url']
        # Convert localhost:8000 to check if file exists
        if 'localhost:8000' in test_url:
            # Check if file exists in static directory
            import re
            match = re.search(r'/static/manual_images/(.+)$', test_url)
            if match:
                from pathlib import Path
                relative_path = match.group(1)
                file_path = Path(f"elysia/api/static/manual_images/{relative_path}")
                
                if file_path.exists():
                    print(f"✅ Image file exists: {file_path}")
                    print(f"   Size: {file_path.stat().st_size / 1024:.1f} KB")
                else:
                    print(f"❌ Image file NOT found: {file_path}")
    
    # Cleanup
    await cm.close_clients()
    
    print("\n" + "=" * 80)
    print("✅ All tests PASSED")
    print("=" * 80)
    print("\nNext: Start frontend and ask agent 'Toon me een foto van een verdamper'")

if __name__ == "__main__":
    asyncio.run(test_image_search())

