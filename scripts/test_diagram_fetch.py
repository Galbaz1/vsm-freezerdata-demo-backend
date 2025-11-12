#!/usr/bin/env python3
"""
Test direct diagram fetching by SMIDO phases.
Validates that diagrams can be queried from AgentInternal using phase filters.
"""

import asyncio
from elysia.util.client import ClientManager
from weaviate.classes.query import Filter


async def test_diagram_fetch():
    """Test fetching diagrams by smido_phases filter (AgentInternal only)."""
    print("=" * 60)
    print("Diagram Fetch Test - SMIDO Phase Matching")
    print("=" * 60)
    
    cm = ClientManager()
    async with cm.connect_to_async_client() as client:
        
        # Note: UserFacing diagrams have EMPTY smido_phases arrays
        # Only AgentInternal has populated phase data
        
        # Test 1: M-phase diagrams (melding)
        print("\nTest 1: Fetching M-phase diagrams (AgentInternal)")
        print("-" * 60)
        
        phases = ["M", "melding"]
        agent_coll = client.collections.get("VSM_DiagramAgentInternal")
        agent_results = await agent_coll.query.fetch_objects(
            filters=Filter.by_property("smido_phases").contains_any(phases),
            limit=5
        )
        
        print(f"AgentInternal diagrams for melding: {len(agent_results.objects)}")
        for obj in agent_results.objects:
            print(f"  - {obj.properties.get('title')}")
        
        # Test 2: P3-phase diagrams (procesparameters)
        print("\nTest 2: Fetching P3-phase diagrams (AgentInternal)")
        print("-" * 60)
        
        phases_p3 = ["P3", "procesparameters"]
        agent_p3 = await agent_coll.query.fetch_objects(
            filters=Filter.by_property("smido_phases").contains_any(phases_p3),
            limit=10
        )
        
        print(f"AgentInternal diagrams for P3: {len(agent_p3.objects)}")
        for obj in agent_p3.objects:
            print(f"  - {obj.properties.get('title')}")
        
        # Validation
        print("\n" + "=" * 60)
        assert len(agent_results.objects) > 0, "Should find M-phase diagrams"
        assert len(agent_p3.objects) > 0, "Should find P3-phase diagrams"
        print("✅ All diagram fetch tests PASSED")
        print(f"✅ M-phase: {len(agent_results.objects)} diagrams")
        print(f"✅ P3-phase: {len(agent_p3.objects)} diagrams")
        print("=" * 60)
    
    await cm.close_clients()


if __name__ == "__main__":
    asyncio.run(test_diagram_fetch())
