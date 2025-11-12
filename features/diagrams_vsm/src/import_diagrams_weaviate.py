#!/usr/bin/env python3
"""
Upload VSM diagram collections to Weaviate Cloud.

Creates two collections:
- VSM_DiagramUserFacing: Simple diagrams for user display (PNG)
- VSM_DiagramAgentInternal: Complex diagrams for agent logic (Mermaid)

Follows official Weaviate docs pattern from docs/adding_data.md
"""

import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Configure, Property, DataType
import os
import json
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
print(f"Weaviate client ready: {client.is_ready()}")

# Delete existing collections if they exist
for collection_name in ["VSM_Diagram", "VSM_DiagramUserFacing", "VSM_DiagramAgentInternal"]:
    try:
        client.collections.delete(collection_name)
        print(f"Deleted existing {collection_name} collection")
    except Exception as e:
        print(f"No existing {collection_name} collection to delete (or error: {e})")

# ============================================================================
# Create VSM_DiagramUserFacing collection
# ============================================================================
print("\n" + "=" * 60)
print("Creating VSM_DiagramUserFacing collection...")
print("=" * 60)

user_facing_collection = client.collections.create(
    name="VSM_DiagramUserFacing",
    description="User-facing diagrams for VSM troubleshooting (PNG display)",
    vector_config=[
        Configure.Vectors.text2vec_weaviate(
            name="default",
            source_properties=["title", "description", "when_to_show"]
        )
    ],
    properties=[
        Property(name="diagram_id", data_type=DataType.TEXT,
                 skip_vectorization=True, filterable=True),
        Property(name="title", data_type=DataType.TEXT),  # Vectorized
        Property(name="description", data_type=DataType.TEXT),  # Vectorized
        Property(name="when_to_show", data_type=DataType.TEXT),  # Vectorized
        Property(name="png_url", data_type=DataType.TEXT,
                 skip_vectorization=True),
        Property(name="png_width", data_type=DataType.INT),
        Property(name="png_height", data_type=DataType.INT),
        Property(name="smido_phases", data_type=DataType.TEXT_ARRAY,
                 skip_vectorization=True, filterable=True),
        Property(name="failure_modes", data_type=DataType.TEXT_ARRAY,
                 skip_vectorization=True, filterable=True),
        Property(name="components", data_type=DataType.TEXT_ARRAY,
                 skip_vectorization=True, filterable=True),
        Property(name="agent_diagram_id", data_type=DataType.TEXT,
                 skip_vectorization=True, filterable=True),  # Link to agent diagram
    ]
)

# Load user-facing diagrams JSONL
with open("features/diagrams_vsm/output/user_facing_diagrams.jsonl", "r") as f:
    user_facing_data = [json.loads(line) for line in f if line.strip()]

print(f"Loaded {len(user_facing_data)} user-facing diagrams from JSONL")

# Batch import user-facing diagrams
with user_facing_collection.batch.fixed_size(batch_size=200) as batch:
    for i, item in enumerate(user_facing_data):
        batch.add_object(item)
        
        if batch.number_errors > 10:
            print("Stopped due to excessive errors.")
            break
        
        if i % 100 == 0:
            print(f"Imported {i} objects...")

# Error handling
failed = user_facing_collection.batch.failed_objects
if failed:
    print(f"Failed: {len(failed)}, First error: {failed[0]}")
else:
    print("All user-facing diagrams imported successfully!")

# Verify
total = user_facing_collection.aggregate.over_all(total_count=True).total_count
print(f"Total objects in VSM_DiagramUserFacing: {total}")

# ============================================================================
# Create VSM_DiagramAgentInternal collection
# ============================================================================
print("\n" + "=" * 60)
print("Creating VSM_DiagramAgentInternal collection...")
print("=" * 60)

agent_collection = client.collections.create(
    name="VSM_DiagramAgentInternal",
    description="Agent-internal diagrams for VSM troubleshooting (Mermaid logic)",
    vector_config=[
        Configure.Vectors.text2vec_weaviate(
            name="default",
            source_properties=["title", "description", "agent_usage"]
        )
    ],
    properties=[
        Property(name="diagram_id", data_type=DataType.TEXT,
                 skip_vectorization=True, filterable=True),
        Property(name="title", data_type=DataType.TEXT),  # Vectorized
        Property(name="description", data_type=DataType.TEXT),  # Vectorized
        Property(name="agent_usage", data_type=DataType.TEXT),  # Vectorized
        Property(name="mermaid_code", data_type=DataType.TEXT,
                 skip_vectorization=True),
        Property(name="source_chunk_id", data_type=DataType.TEXT,
                 skip_vectorization=True, filterable=True),
        Property(name="smido_phases", data_type=DataType.TEXT_ARRAY,
                 skip_vectorization=True, filterable=True),
        Property(name="failure_modes", data_type=DataType.TEXT_ARRAY,
                 skip_vectorization=True, filterable=True),
        Property(name="diagram_type", data_type=DataType.TEXT,
                 skip_vectorization=True, filterable=True),
    ]
)

# Load agent-internal diagrams JSONL
with open("features/diagrams_vsm/output/agent_internal_diagrams.jsonl", "r") as f:
    agent_data = [json.loads(line) for line in f if line.strip()]

print(f"Loaded {len(agent_data)} agent-internal diagrams from JSONL")

# Batch import agent-internal diagrams
with agent_collection.batch.fixed_size(batch_size=200) as batch:
    for i, item in enumerate(agent_data):
        batch.add_object(item)
        
        if batch.number_errors > 10:
            print("Stopped due to excessive errors.")
            break
        
        if i % 100 == 0:
            print(f"Imported {i} objects...")

# Error handling
failed = agent_collection.batch.failed_objects
if failed:
    print(f"Failed: {len(failed)}, First error: {failed[0]}")
else:
    print("All agent-internal diagrams imported successfully!")

# Verify
total = agent_collection.aggregate.over_all(total_count=True).total_count
print(f"Total objects in VSM_DiagramAgentInternal: {total}")

# Sample queries
print("\n" + "=" * 60)
print("Sample queries:")
print("=" * 60)

user_sample = user_facing_collection.query.fetch_objects(limit=3)
print(f"\nUser-facing diagrams:")
for obj in user_sample.objects:
    print(f"  - {obj.properties.get('title', 'N/A')} ({obj.properties.get('diagram_id', 'N/A')})")

agent_sample = agent_collection.query.fetch_objects(limit=3)
print(f"\nAgent-internal diagrams:")
for obj in agent_sample.objects:
    print(f"  - {obj.properties.get('title', 'N/A')} ({obj.properties.get('diagram_id', 'N/A')})")

client.close()
print("\n✅ Diagram collections upload complete!")
print(f"   - VSM_DiagramUserFacing: {len(user_facing_data)} diagrams")
print(f"   - VSM_DiagramAgentInternal: {len(agent_data)} diagrams")
