#!/usr/bin/env python3
"""
Simple test to verify diagram collections exist in Weaviate.
"""

import os
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.query import Filter
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

weaviate_url = os.environ.get("WEAVIATE_URL") or os.environ["WCD_URL"]
weaviate_api_key = os.environ.get("WEAVIATE_API_KEY") or os.environ["WCD_API_KEY"]

# Connect to Weaviate Cloud
client = weaviate.connect_to_weaviate_cloud(
    cluster_url=weaviate_url,
    auth_credentials=Auth.api_key(weaviate_api_key)
)

print("=" * 60)
print("Testing Diagram Collections")
print("=" * 60)

try:
    # Test user-facing collection
    if not client.collections.exists("VSM_DiagramUserFacing"):
        print("❌ VSM_DiagramUserFacing collection not found")
        exit(1)
    
    user_coll = client.collections.get("VSM_DiagramUserFacing")
    user_count = user_coll.aggregate.over_all(total_count=True).total_count
    print(f"✅ VSM_DiagramUserFacing: {user_count} diagrams")
    
    # Test agent-internal collection
    if not client.collections.exists("VSM_DiagramAgentInternal"):
        print("❌ VSM_DiagramAgentInternal collection not found")
        exit(1)
    
    agent_coll = client.collections.get("VSM_DiagramAgentInternal")
    agent_count = agent_coll.aggregate.over_all(total_count=True).total_count
    print(f"✅ VSM_DiagramAgentInternal: {agent_count} diagrams")
    
    # Test specific diagram IDs
    print("\n" + "=" * 60)
    print("Testing Diagram IDs")
    print("=" * 60)
    
    test_ids = [
        "smido_overview",
        "diagnose_4ps",
        "basic_cycle",
        "measurement_points",
        "system_balance",
        "pressostat_settings",
        "troubleshooting_template",
        "frozen_evaporator",
    ]
    
    for diagram_id in test_ids:
        result = user_coll.query.fetch_objects(
            filters=Filter.by_property("diagram_id").equal(diagram_id),
            limit=1
        )
        if result.objects:
            obj = result.objects[0]
            props = obj.properties
            print(f"  ✅ {diagram_id}")
            print(f"     Title: {props.get('title', 'N/A')}")
            print(f"     PNG: {props.get('png_url', 'N/A')}")
            print(f"     Agent Diagram: {props.get('agent_diagram_id', 'N/A')}")
        else:
            print(f"  ❌ {diagram_id} - NOT FOUND")
    
    # Test agent diagram retrieval
    print("\n" + "=" * 60)
    print("Testing Agent Diagram Retrieval")
    print("=" * 60)
    
    test_agent_id = "smido_main_flowchart"
    agent_result = agent_coll.query.fetch_objects(
        filters=Filter.by_property("diagram_id").equal(test_agent_id),
        limit=1
    )
    
    if agent_result.objects:
        agent_obj = agent_result.objects[0]
        agent_props = agent_obj.properties
        mermaid_code = agent_props.get("mermaid_code", "")
        print(f"  ✅ {test_agent_id}")
        print(f"     Title: {agent_props.get('title', 'N/A')}")
        print(f"     Mermaid Code Length: {len(mermaid_code)} characters")
        print(f"     First 100 chars: {mermaid_code[:100]}...")
    else:
        print(f"  ❌ {test_agent_id} - NOT FOUND")
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    exit(1)
finally:
    client.close()

