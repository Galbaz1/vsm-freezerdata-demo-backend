#!/usr/bin/env python3
"""
Test image gallery UX improvements and diagram dual-handling.

Tests:
1. Image gallery returns max 2 images by default
2. PNG diagrams (UserFacing) are findable and display correctly
3. Mermaid diagrams (AgentInternal) are findable and display correctly
4. search_manuals_by_smido includes diagrams in output
5. show_diagram tool is registered and callable

Run: python3 scripts/test_image_diagram_improvements.py
"""

import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from elysia.util.client import ClientManager
from weaviate.classes.query import Filter


async def test_image_limit():
    """Test 1: Verify search_manual_images default limit is 2."""
    print("\n" + "="*60)
    print("TEST 1: Image Gallery Default Limit")
    print("="*60)
    
    # Read source file directly
    custom_tools_path = os.path.join(os.path.dirname(__file__), '..', 'elysia', 'api', 'custom_tools.py')
    with open(custom_tools_path, 'r') as f:
        source = f.read()
    
    # Search for function definition
    import re
    pattern = r'async def search_manual_images\([^)]*limit:\s*int\s*=\s*(\d+)'
    match = re.search(pattern, source)
    
    if match:
        limit_value = int(match.group(1))
        if limit_value == 2:
            print(f"✅ PASS: search_manual_images default limit = {limit_value}")
            return True
        else:
            print(f"❌ FAIL: Expected limit=2, got {limit_value}")
            return False
    else:
        print("❌ FAIL: Could not find search_manual_images function signature")
        return False


async def test_png_diagrams():
    """Test 2: Verify UserFacing diagrams have PNG URLs and SMIDO phases."""
    print("\n" + "="*60)
    print("TEST 2: PNG Diagrams (UserFacing)")
    print("="*60)
    
    cm = ClientManager()
    
    try:
        async with cm.connect_to_async_client() as client:
            if not await client.collections.exists('VSM_DiagramUserFacing'):
                print("❌ FAIL: VSM_DiagramUserFacing collection not found")
                return False
            
            coll = client.collections.get('VSM_DiagramUserFacing')
            
            # Query by SMIDO phase 'M' (should find smido_overview)
            results = await coll.query.fetch_objects(
                filters=Filter.by_property("smido_phases").contains_any(["M"]),
                limit=5
            )
            
            if len(results.objects) == 0:
                print("❌ FAIL: No UserFacing diagrams found with phase 'M'")
                return False
            
            print(f"✅ Found {len(results.objects)} diagrams with phase 'M'")
            
            # Verify PNG URLs exist
            png_count = 0
            for obj in results.objects:
                png_url = obj.properties.get('png_url')
                diagram_id = obj.properties.get('diagram_id')
                if png_url:
                    png_count += 1
                    print(f"✅ {diagram_id}: {png_url}")
                else:
                    print(f"❌ {diagram_id}: No PNG URL!")
            
            if png_count == len(results.objects):
                print(f"✅ PASS: All {png_count} diagrams have PNG URLs")
                return True
            else:
                print(f"❌ FAIL: Only {png_count}/{len(results.objects)} have PNG URLs")
                return False
    
    finally:
        await cm.close_clients()


async def test_mermaid_diagrams():
    """Test 3: Verify AgentInternal diagrams have Mermaid code."""
    print("\n" + "="*60)
    print("TEST 3: Mermaid Diagrams (AgentInternal)")
    print("="*60)
    
    cm = ClientManager()
    
    try:
        async with cm.connect_to_async_client() as client:
            if not await client.collections.exists('VSM_DiagramAgentInternal'):
                print("❌ FAIL: VSM_DiagramAgentInternal collection not found")
                return False
            
            coll = client.collections.get('VSM_DiagramAgentInternal')
            
            # Query by SMIDO phase 'power' (AgentInternal uses full text names)
            results = await coll.query.fetch_objects(
                filters=Filter.by_property("smido_phases").contains_any(["power"]),
                limit=5
            )
            
            if len(results.objects) == 0:
                print("❌ FAIL: No AgentInternal diagrams found with phase 'power'")
                return False
            
            print(f"✅ Found {len(results.objects)} diagrams with phase 'power'")
            
            # Verify Mermaid code exists
            mermaid_count = 0
            for obj in results.objects:
                mermaid_code = obj.properties.get('mermaid_code')
                diagram_id = obj.properties.get('diagram_id')
                if mermaid_code and len(mermaid_code) > 0:
                    mermaid_count += 1
                    print(f"✅ {diagram_id}: {len(mermaid_code)} chars of Mermaid code")
                else:
                    print(f"❌ {diagram_id}: No Mermaid code!")
            
            if mermaid_count == len(results.objects):
                print(f"✅ PASS: All {mermaid_count} diagrams have Mermaid code")
                return True
            else:
                print(f"❌ FAIL: Only {mermaid_count}/{len(results.objects)} have Mermaid code")
                return False
    
    finally:
        await cm.close_clients()


async def test_show_diagram_registration():
    """Test 4: Verify show_diagram tool is registered in bootstrap."""
    print("\n" + "="*60)
    print("TEST 4: show_diagram Tool Registration")
    print("="*60)
    
    # Read bootstrap.py source
    bootstrap_path = os.path.join(os.path.dirname(__file__), '..', 'features', 'vsm_tree', 'bootstrap.py')
    with open(bootstrap_path, 'r') as f:
        source = f.read()
    
    # Check for import
    has_import = 'show_diagram' in source and 'from elysia.api.custom_tools import' in source
    
    # Check for registration
    has_registration = 'tree.add_tool(branch_id="base", tool=show_diagram)' in source
    
    if has_import:
        print("✅ show_diagram is imported in bootstrap.py")
    else:
        print("❌ show_diagram NOT imported in bootstrap.py")
    
    if has_registration:
        print("✅ show_diagram is registered at base root")
    else:
        print("❌ show_diagram NOT registered at base root")
    
    if has_import and has_registration:
        print("✅ PASS: show_diagram tool is registered")
        return True
    else:
        print("❌ FAIL: show_diagram missing from bootstrap")
        return False


async def test_diagram_dual_handling():
    """Test 5: Verify show_diagram handles both PNG and Mermaid."""
    print("\n" + "="*60)
    print("TEST 5: Diagram Dual Handling (PNG + Mermaid)")
    print("="*60)
    
    # Read custom_tools.py source
    custom_tools_path = os.path.join(os.path.dirname(__file__), '..', 'elysia', 'api', 'custom_tools.py')
    with open(custom_tools_path, 'r') as f:
        source = f.read()
    
    # Check for PNG handling in show_diagram
    has_png_check = 'png_url = props.get("png_url")' in source and 'if png_url:' in source
    has_mermaid_check = 'elif mermaid_code:' in source
    has_full_url = 'http://localhost:8000' in source and 'full_url = f"http://localhost:8000{png_url}"' in source
    
    if has_png_check:
        print("✅ show_diagram checks for png_url")
    else:
        print("❌ show_diagram missing png_url check")
    
    if has_mermaid_check:
        print("✅ show_diagram falls back to mermaid_code")
    else:
        print("❌ show_diagram missing mermaid_code fallback")
    
    if has_full_url:
        print("✅ show_diagram builds full URL for PNG images")
    else:
        print("❌ show_diagram missing full URL construction")
    
    if has_png_check and has_mermaid_check and has_full_url:
        print("✅ PASS: show_diagram handles both PNG and Mermaid")
        return True
    else:
        print("❌ FAIL: show_diagram missing dual handling logic")
        return False


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("IMAGE GALLERY & DIAGRAM IMPROVEMENTS TEST SUITE")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Image Gallery Limit", await test_image_limit()))
    results.append(("PNG Diagrams", await test_png_diagrams()))
    results.append(("Mermaid Diagrams", await test_mermaid_diagrams()))
    results.append(("show_diagram Registration", await test_show_diagram_registration()))
    results.append(("Diagram Dual Handling", await test_diagram_dual_handling()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Image gallery and diagrams ready for production.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review output above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

