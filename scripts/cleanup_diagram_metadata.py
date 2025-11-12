#!/usr/bin/env python3
"""
Clean up diagram metadata and re-preprocess collections.
Run with: source scripts/activate_env.sh && python3 scripts/cleanup_diagram_metadata.py
"""

import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.query import Filter
import os
from dotenv import load_dotenv

load_dotenv()

client = weaviate.connect_to_weaviate_cloud(
    cluster_url=os.environ['WCD_URL'],
    auth_credentials=Auth.api_key(os.environ['WCD_API_KEY'])
)

print("=" * 60)
print("Cleaning up diagram metadata")
print("=" * 60)

meta_coll = client.collections.get('ELYSIA_METADATA__')

# Delete old VSM_Diagram metadata
result = meta_coll.query.fetch_objects(
    filters=Filter.by_property('name').equal('VSM_Diagram'),
    limit=1
)

if result.objects:
    for obj in result.objects:
        meta_coll.data.delete_by_id(obj.uuid)
        print(f"✅ Deleted old VSM_Diagram metadata (UUID: {obj.uuid})")
else:
    print("ℹ️  No old VSM_Diagram metadata found (already cleaned)")

# Check current state
result = meta_coll.query.fetch_objects(limit=20)
print("\nCurrent collections in ELYSIA_METADATA__:")
for obj in result.objects:
    name = obj.properties.get('name', 'N/A')
    print(f"  - {name}")

client.close()

print("\n" + "=" * 60)
print("Now run preprocessing:")
print("python3 scripts/preprocess_collections.py --collections VSM_DiagramUserFacing VSM_DiagramAgentInternal")
print("=" * 60)

