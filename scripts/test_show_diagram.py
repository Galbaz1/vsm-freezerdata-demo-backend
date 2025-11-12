#!/usr/bin/env python3
"""
Test script for show_diagram tool.

Tests:
- Diagram fetching from Weaviate
- PNG path resolution
- Tool execution with all diagram IDs
- Agent context loading
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from elysia.util.client import ClientManager
from elysia.api.custom_tools import show_diagram
from elysia.tree.tree import Tree
from elysia.tree.tree_data import TreeData
from elysia.api.utils.config import Config

# All available diagram IDs
DIAGRAM_IDS = [
    "smido_overview",
    "diagnose_4ps",
    "basic_cycle",
    "measurement_points",
    "system_balance",
    "pressostat_settings",
    "troubleshooting_template",
    "frozen_evaporator",
]

async def test_weaviate_collections():
    """Test that both collections exist and have data."""
    print("=" * 60)
    print("Testing Weaviate Collections")
    print("=" * 60)
    
    client_manager = ClientManager()
    
    if not client_manager.is_client:
        print("ERROR: Weaviate client not configured")
        return False
    
    async with client_manager.connect_to_async_client() as client:
        # Check user-facing collection
        if not await client.collections.exists("VSM_DiagramUserFacing"):
            print("ERROR: VSM_DiagramUserFacing collection not found")
            return False
        
        user_coll = client.collections.get("VSM_DiagramUserFacing")
        user_count = user_coll.aggregate.over_all(total_count=True).total_count
        print(f"✓ VSM_DiagramUserFacing: {user_count} diagrams")
        
        # Check agent-internal collection
        if not await client.collections.exists("VSM_DiagramAgentInternal"):
            print("ERROR: VSM_DiagramAgentInternal collection not found")
            return False
        
        agent_coll = client.collections.get("VSM_DiagramAgentInternal")
        agent_count = agent_coll.aggregate.over_all(total_count=True).total_count
        print(f"✓ VSM_DiagramAgentInternal: {agent_count} diagrams")
        
        # Verify all diagram IDs exist
        print("\nVerifying diagram IDs...")
        missing = []
        for diagram_id in DIAGRAM_IDS:
            result = await user_coll.query.fetch_objects(
                filters=Filter.by_property("diagram_id").equal(diagram_id),
                limit=1
            )
            if result.objects:
                print(f"  ✓ {diagram_id}")
            else:
                print(f"  ✗ {diagram_id} - NOT FOUND")
                missing.append(diagram_id)
        
        if missing:
            print(f"\nERROR: Missing diagrams: {', '.join(missing)}")
            return False
        
        return True

async def test_png_paths():
    """Test that PNG files exist in static directory."""
    print("\n" + "=" * 60)
    print("Testing PNG File Paths")
    print("=" * 60)
    
    static_dir = project_root / "elysia" / "api" / "static" / "diagrams"
    
    if not static_dir.exists():
        print(f"ERROR: Static directory not found: {static_dir}")
        return False
    
    missing = []
    for diagram_id in DIAGRAM_IDS:
        png_path = static_dir / f"{diagram_id}.png"
        if png_path.exists():
            print(f"  ✓ {diagram_id}.png")
        else:
            print(f"  ✗ {diagram_id}.png - NOT FOUND")
            missing.append(diagram_id)
    
    if missing:
        print(f"\nERROR: Missing PNG files: {', '.join(missing)}")
        return False
    
    return True

async def test_tool_execution():
    """Test show_diagram tool execution."""
    print("\n" + "=" * 60)
    print("Testing Tool Execution")
    print("=" * 60)
    
    # Create minimal tree data
    config = Config()
    tree_data = TreeData(config)
    client_manager = ClientManager()
    
    if not client_manager.is_client:
        print("ERROR: Weaviate client not configured")
        return False
    
    # Test with first diagram
    test_diagram_id = DIAGRAM_IDS[0]
    print(f"\nTesting show_diagram('{test_diagram_id}')...")
    
    results = []
    errors = []
    
    async for result in show_diagram(
        diagram_id=test_diagram_id,
        tree_data=tree_data,
        client_manager=client_manager
    ):
        results.append(result)
        if hasattr(result, 'message') and 'error' in result.message.lower():
            errors.append(result.message)
    
    if errors:
        print(f"  ✗ Errors: {errors}")
        return False
    
    # Check that Result was yielded
    result_objects = [r for r in results if isinstance(r, Result)]
    if not result_objects:
        print("  ✗ No Result object yielded")
        return False
    
    result = result_objects[0]
    objects = result.objects
    
    if not objects:
        print("  ✗ Result has no objects")
        return False
    
    diagram_obj = objects[0]
    
    # Verify structure
    required_keys = ["diagram_id", "png_url", "title", "description"]
    missing_keys = [k for k in required_keys if k not in diagram_obj]
    
    if missing_keys:
        print(f"  ✗ Missing keys: {', '.join(missing_keys)}")
        return False
    
    print(f"  ✓ Diagram ID: {diagram_obj['diagram_id']}")
    print(f"  ✓ PNG URL: {diagram_obj['png_url']}")
    print(f"  ✓ Title: {diagram_obj['title']}")
    
    # Check agent context loading
    if hasattr(tree_data.environment, 'hidden_environment'):
        mermaid_key = f"diagram_{test_diagram_id}_mermaid"
        if mermaid_key in tree_data.environment.hidden_environment:
            mermaid_code = tree_data.environment.hidden_environment[mermaid_key]
            print(f"  ✓ Agent Mermaid loaded: {len(mermaid_code)} characters")
        else:
            print(f"  ⚠ Agent Mermaid not found in hidden_environment")
    
    return True

async def test_all_diagrams():
    """Test all diagram IDs."""
    print("\n" + "=" * 60)
    print("Testing All Diagram IDs")
    print("=" * 60)
    
    client_manager = ClientManager()
    config = Config()
    
    success_count = 0
    
    for diagram_id in DIAGRAM_IDS:
        tree_data = TreeData(config)
        
        try:
            results = []
            async for result in show_diagram(
                diagram_id=diagram_id,
                tree_data=tree_data,
                client_manager=client_manager
            ):
                results.append(result)
            
            # Check for errors
            has_error = any(
                hasattr(r, 'message') and 'error' in r.message.lower()
                for r in results
            )
            
            if has_error:
                print(f"  ✗ {diagram_id}")
            else:
                print(f"  ✓ {diagram_id}")
                success_count += 1
        except Exception as e:
            print(f"  ✗ {diagram_id} - Exception: {e}")
    
    print(f"\nSuccess: {success_count}/{len(DIAGRAM_IDS)} diagrams")
    return success_count == len(DIAGRAM_IDS)

async def main():
    """Run all tests."""
    print("=" * 60)
    print("show_diagram Tool Test Suite")
    print("=" * 60)
    
    # Import Filter here to avoid issues
    from weaviate.classes.query import Filter
    from elysia.objects import Result
    
    tests = [
        ("Weaviate Collections", test_weaviate_collections),
        ("PNG File Paths", test_png_paths),
        ("Tool Execution", test_tool_execution),
        ("All Diagrams", test_all_diagrams),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\nERROR in {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

