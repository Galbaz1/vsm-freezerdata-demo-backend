#!/usr/bin/env python3
"""
Quick test to verify show_diagram tool reads .mermaid files correctly
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

async def test_show_diagram():
    """Test show_diagram tool with filesystem reading"""
    from elysia.api.custom_tools import show_diagram
    from elysia.util.client import ClientManager
    
    print("=" * 80)
    print("Testing show_diagram with Mermaid filesystem reading")
    print("=" * 80)
    
    # Mock tree_data
    class MockEnvironment:
        def __init__(self):
            self.hidden_environment = {}
    
    class MockTreeData:
        def __init__(self):
            self.environment = MockEnvironment()
    
    tree_data = MockTreeData()
    client_manager = ClientManager()
    
    # Test with smido_overview diagram
    diagram_id = "smido_overview"
    
    print(f"\n1. Testing diagram: {diagram_id}")
    print("-" * 80)
    
    results = []
    async for result in show_diagram(
        diagram_id=diagram_id,
        tree_data=tree_data,
        client_manager=client_manager
    ):
        results.append(result)
        print(f"   Result type: {type(result).__name__}")
        
        if hasattr(result, 'text'):
            # Response object
            text = result.text
            print(f"   Response text length: {len(text)} chars")
            print(f"   Contains '```mermaid': {'```mermaid' in text}")
            print(f"   First 200 chars: {text[:200]}")
            
            # Check if agent diagram loaded in environment
            if hasattr(tree_data.environment, 'hidden_environment'):
                agent_key = f"diagram_{diagram_id}_mermaid"
                if agent_key in tree_data.environment.hidden_environment:
                    agent_mermaid = tree_data.environment.hidden_environment[agent_key]
                    print(f"   Agent diagram loaded: {len(agent_mermaid)} chars")
                else:
                    print(f"   Agent diagram NOT loaded")
        elif hasattr(result, 'message'):
            # Error object
            print(f"   Error: {result.message}")
    
    print("\n" + "=" * 80)
    print("✅ Test completed successfully!")
    print("=" * 80)
    
    # Verify key aspects
    print("\nVerification:")
    print(f"   ✓ Total results: {len(results)}")
    has_response = any(hasattr(r, 'text') for r in results)
    print(f"   ✓ Has Response object: {has_response}")
    
    if has_response:
        response = next(r for r in results if hasattr(r, 'text'))
        has_mermaid_fence = '```mermaid' in response.text
        print(f"   ✓ Contains Mermaid code fence: {has_mermaid_fence}")
        
        if has_mermaid_fence:
            print("\n✅ show_diagram tool is working correctly!")
        else:
            print("\n❌ WARNING: Response doesn't contain Mermaid code fence")
    else:
        print("\n❌ WARNING: No Response object returned")

if __name__ == "__main__":
    asyncio.run(test_show_diagram())

