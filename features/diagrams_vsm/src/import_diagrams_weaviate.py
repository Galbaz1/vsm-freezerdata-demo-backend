#!/usr/bin/env python3
"""
Upload VSM_Diagram collection to Weaviate Cloud.
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

weaviate_url = os.environ["WEAVIATE_URL"]
weaviate_api_key = os.environ["WEAVIATE_API_KEY"]

# Connect to Weaviate Cloud
client = weaviate.connect_to_weaviate_cloud(
    cluster_url=weaviate_url,
    auth_credentials=Auth.api_key(weaviate_api_key)
)
print(f"Weaviate client ready: {client.is_ready()}")

# Delete existing collection if it exists
try:
    client.collections.delete("VSM_Diagram")
    print("Deleted existing VSM_Diagram collection")
except Exception as e:
    print(f"No existing collection to delete")

# Create collection
collection = client.collections.create(
    name="VSM_Diagram",
    description="Visual logic diagrams for VSM troubleshooting (Mermaid format)",
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
        Property(name="source_manual", data_type=DataType.TEXT,
                 skip_vectorization=True, filterable=True),
        Property(name="page_reference", data_type=DataType.TEXT,
                 skip_vectorization=True),
        Property(name="smido_phases", data_type=DataType.TEXT_ARRAY,
                 skip_vectorization=True, filterable=True),
        Property(name="failure_modes", data_type=DataType.TEXT_ARRAY,
                 skip_vectorization=True, filterable=True),
        Property(name="components", data_type=DataType.TEXT_ARRAY,
                 skip_vectorization=True, filterable=True),
        Property(name="diagram_type", data_type=DataType.TEXT,
                 skip_vectorization=True, filterable=True),
        Property(name="created_date", data_type=DataType.TEXT,
                 skip_vectorization=True),
    ]
)

# Load agent-generated JSONL
with open("features/diagrams_vsm/output/diagrams_metadata.jsonl", "r") as f:
    data = [json.loads(line) for line in f if line.strip()]

print(f"Loaded {len(data)} diagrams from JSONL")

# Batch import
with collection.batch.fixed_size(batch_size=200) as batch:
    for i, item in enumerate(data):
        batch.add_object(item)
        
        if batch.number_errors > 10:
            print("Stopped due to excessive errors.")
            break
        
        if i % 100 == 0:
            print(f"Imported {i} objects...")

# Error handling
failed = collection.batch.failed_objects
if failed:
    print(f"Failed: {len(failed)}, First error: {failed[0]}")
else:
    print("All objects imported successfully!")

# Verify
total = collection.aggregate.over_all(total_count=True).total_count
print(f"Total objects in VSM_Diagram: {total}")

# Sample query
sample = collection.query.fetch_objects(limit=3)
print(f"\nSample diagrams:")
for obj in sample.objects:
    print(f"  - {obj.properties.get('title', 'N/A')}")

client.close()
print("\n✅ VSM_Diagram upload complete!")

