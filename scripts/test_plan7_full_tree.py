#!/usr/bin/env python3
"""
Plan 7: A3 Frozen Evaporator - Full Tree Execution Test

Tests complete SMIDO workflow with A3 scenario using full tree execution.
Verifies all data sources integrate correctly, tools execute properly, and agent provides correct diagnosis.
"""

import asyncio
import sys
import warnings
from datetime import datetime
from pathlib import Path

# Suppress ResourceWarnings for cleaner output
warnings.filterwarnings("ignore", category=ResourceWarning)

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from elysia import Tree
from elysia.util.client import ClientManager
from features.vsm_tree.smido_tree import create_vsm_tree

# VSM collection names
VSM_COLLECTIONS = [
    "VSM_TelemetryEvent",
    "VSM_VlogCase",
    "VSM_VlogClip",
    "VSM_ManualSections",
    "VSM_Diagram",
    "VSM_WorldStateSnapshot",
]


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_subsection(title: str):
    """Print a formatted subsection header."""
    print(f"\n--- {title} ---")


async def test_a3_full_tree_execution():
    """
    Test complete A3 frozen evaporator scenario with full tree execution.
    """
    print_section("Plan 7: A3 Frozen Evaporator - Full Tree Execution Test")
    
    # Test configuration
    asset_id = "135_1570"
    user_query = "Koelcel bereikt temperatuur niet"
    
    print(f"\n📋 Test Configuration:")
    print(f"   Asset ID: {asset_id}")
    print(f"   User Query: '{user_query}'")
    print(f"   Collections: {', '.join(VSM_COLLECTIONS)}")
    
    # Initialize tree
    print_subsection("1. Tree Initialization")
    try:
        tree = create_vsm_tree()
        print("✅ Tree created successfully")
        print(f"   Base Model: {tree.settings.BASE_MODEL}")
        print(f"   Complex Model: {tree.settings.COMPLEX_MODEL}")
        print(f"   Agent Description: {tree.tree_data.atlas.agent_description[:80]}...")
    except Exception as e:
        print(f"❌ Error creating tree: {e}")
        return False
    
    # Verify collections are accessible
    print_subsection("2. Collection Verification")
    try:
        cm = ClientManager()
        async with cm.connect_to_async_client() as client:
            for coll_name in VSM_COLLECTIONS:
                try:
                    collection = client.collections.get(coll_name)
                    result = await collection.aggregate.over_all(total_count=True)
                    count = result.total_count
                    print(f"   ✅ {coll_name}: {count} objects")
                except Exception as e:
                    print(f"   ⚠️  {coll_name}: Error accessing - {e}")
        await cm.close_clients()
    except Exception as e:
        print(f"   ⚠️  Error verifying collections: {e}")
    
    # Execute tree with A3 scenario query
    print_subsection("3. Full Tree Execution")
    print(f"\n🚀 Executing tree with query: '{user_query}'")
    print("   (This may take 30-60 seconds for full LLM-driven execution...)")
    
    start_time = datetime.now()
    
    try:
        # Execute tree - this will use LLM to decide which tools to call
        response, objects = tree.run(
            user_query,
            collection_names=VSM_COLLECTIONS,
            close_clients_after_completion=True
        )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        print(f"\n✅ Tree execution completed in {execution_time:.2f} seconds")
        
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        print(f"\n❌ Error during tree execution: {e}")
        print(f"   Execution time: {execution_time:.2f} seconds")
        import traceback
        traceback.print_exc()
        return False
    
    # Analyze results
    print_subsection("4. Results Analysis")
    
    # Check response
    if response:
        print(f"\n📝 Agent Response ({len(response)} chars):")
        print(f"   {response[:200]}..." if len(response) > 200 else f"   {response}")
    else:
        print("   ⚠️  No response generated")
    
    # Check retrieved objects
    if objects:
        print(f"\n📦 Retrieved Objects: {len(objects)} groups")
        for i, obj_group in enumerate(objects):
            if isinstance(obj_group, list) and len(obj_group) > 0:
                print(f"   Group {i+1}: {len(obj_group)} objects")
                # Show first object keys
                if isinstance(obj_group[0], dict):
                    keys = list(obj_group[0].keys())[:5]
                    print(f"      Keys: {', '.join(keys)}...")
            else:
                print(f"   Group {i+1}: {type(obj_group)}")
    else:
        print("   ⚠️  No objects retrieved")
    
    # Verify A3-specific data was retrieved
    print_subsection("5. A3 Scenario Verification")
    
    a3_indicators = {
        "frozen_evaporator": False,
        "alarms": False,
        "worldstate": False,
        "vlog_case": False,
        "manual_sections": False,
    }
    
    # Check response for A3 indicators
    response_lower = response.lower() if response else ""
    if any(term in response_lower for term in ["verdamper", "frozen", "bevroren", "ontdooi", "defrost"]):
        a3_indicators["frozen_evaporator"] = True
        print("   ✅ Frozen evaporator mentioned in response")
    
    # Check objects for A3 data
    if objects:
        for obj_group in objects:
            if isinstance(obj_group, list):
                for obj in obj_group:
                    if isinstance(obj, dict):
                        # Check for alarm data
                        if "severity" in obj or "alarm" in str(obj).lower():
                            a3_indicators["alarms"] = True
                        
                        # Check for worldstate data
                        if "current_state" in obj or "worldstate" in str(obj).lower():
                            a3_indicators["worldstate"] = True
                        
                        # Check for vlog case
                        if "vlog" in str(obj).lower() or "a3" in str(obj).lower():
                            a3_indicators["vlog_case"] = True
                        
                        # Check for manual sections
                        if "manual" in str(obj).lower() or "smido" in str(obj).lower():
                            a3_indicators["manual_sections"] = True
    
    # Print verification summary
    print(f"\n📊 A3 Scenario Indicators:")
    for indicator, found in a3_indicators.items():
        status = "✅" if found else "⏳"
        print(f"   {status} {indicator.replace('_', ' ').title()}: {'Found' if found else 'Not found'}")
    
    # Success criteria
    print_subsection("6. Success Criteria")
    
    success_criteria = {
        "Tree executed successfully": execution_time < 120,  # Should complete in <2 minutes
        "Response generated": bool(response),
        "Objects retrieved": bool(objects),
        "Frozen evaporator detected": a3_indicators["frozen_evaporator"],
    }
    
    all_passed = all(success_criteria.values())
    
    for criterion, passed in success_criteria.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {criterion}")
    
    # Final summary
    print_section("Test Summary")
    
    if all_passed:
        print("✅ All critical success criteria passed!")
        print(f"\n📈 Execution Statistics:")
        print(f"   Execution Time: {execution_time:.2f} seconds")
        print(f"   Response Length: {len(response) if response else 0} characters")
        print(f"   Objects Retrieved: {len(objects) if objects else 0} groups")
        print(f"\n🎉 Plan 7 full tree execution test PASSED!")
        return True
    else:
        print("⚠️  Some success criteria not met, but tree execution completed.")
        print(f"\n📈 Execution Statistics:")
        print(f"   Execution Time: {execution_time:.2f} seconds")
        print(f"   Response Length: {len(response) if response else 0} characters")
        print(f"   Objects Retrieved: {len(objects) if objects else 0} groups")
        print(f"\n💡 Note: This is a full LLM-driven execution. Results may vary.")
        return False


async def main():
    """Main test execution."""
    try:
        success = await test_a3_full_tree_execution()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

