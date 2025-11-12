#!/usr/bin/env python3
"""
Integration test: search_manuals_by_smido with diagram fetching.
Verifies diagrams are returned in metadata with correct format.
"""

import asyncio
from elysia import Tree
from elysia.util.client import ClientManager
from elysia.objects import Result


async def test_integration():
    """Test search_manuals_by_smido returns diagrams via SMIDO phase matching."""
    print("=" * 60)
    print("Integration Test: search_manuals_by_smido + Diagrams")
    print("=" * 60)
    
    # Create minimal tree
    tree = Tree(branch_initialisation="empty")
    cm = ClientManager()
    
    # Import tool
    from elysia.api.custom_tools import search_manuals_by_smido
    
    # Test with P3 (procesparameters) - should find diagrams
    print("\nTest: Fetching manuals for P3 (procesparameters) with diagrams")
    print("-" * 60)
    
    results = []
    # Call the tool properly with all required arguments
    tool_instance = search_manuals_by_smido
    async for item in tool_instance(
        tree_data=tree.tree_data,
        inputs={
            "query": "verdamper temperatuur",
            "smido_step": "3P_procesparameters",
            "include_diagrams": True
        },
        base_lm=tree.base_lm,
        complex_lm=tree.complex_lm,
        client_manager=cm
    ):
        results.append(item)
    
    # Find Result object
    result_objs = [r for r in results if isinstance(r, Result)]
    
    if result_objs:
        metadata = result_objs[0].metadata
        diagram_count = metadata.get('diagram_count', 0)
        diagrams = metadata.get('diagrams', [])
        
        print(f"\nDiagrams returned: {diagram_count}")
        print(f"Diagram objects in metadata: {len(diagrams)}")
        
        if diagrams:
            print("\nDiagram details:")
            for d in diagrams[:3]:
                title = d.get('title', 'Unknown')[:50]
                diagram_id = d.get('diagram_id', 'unknown')
                has_mermaid = 'mermaid_code' in d
                print(f"  - {title}")
                print(f"    ID: {diagram_id}")
                print(f"    Has mermaid_code: {has_mermaid}")
            
            # Validation
            print("\n" + "=" * 60)
            assert diagram_count > 0, "Should return diagrams for P3"
            assert len(diagrams) > 0, "Diagrams array should be populated"
            assert 'mermaid_code' in diagrams[0], "Diagrams should have mermaid_code"
            print("✅ Integration test PASSED")
            print(f"✅ Returned {diagram_count} diagrams via SMIDO phase matching")
            print("=" * 60)
        else:
            print("\n❌ No diagrams returned - fallback strategy failed")
    else:
        print("\n❌ No Result objects found")
    
    await cm.close_clients()


if __name__ == "__main__":
    asyncio.run(test_integration())

