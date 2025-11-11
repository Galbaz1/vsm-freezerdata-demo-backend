#!/usr/bin/env python3
"""
Upload VSM_WorldStateSnapshot collection to Weaviate Cloud.
Reference patterns for AnalyzeSensorPattern tool.
Follows official Weaviate docs pattern from docs/adding_data.md
"""

import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.query import Filter
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

# Create collection
collection = client.collections.create(
    name="VSM_WorldStateSnapshot",
    description="Reference WorldState patterns for 'uit balans' detection (AnalyzeSensorPattern tool)",
    vector_config=[
        Configure.Vectors.text2vec_weaviate(
            name="default",
            source_properties=["typical_pattern"]
        )
    ],
    properties=[
        Property(name="snapshot_id", data_type=DataType.TEXT,
                 skip_vectorization=True, filterable=True),
        Property(name="failure_mode", data_type=DataType.TEXT,
                 skip_vectorization=True, filterable=True),
        Property(name="worldstate_json", data_type=DataType.TEXT,
                 skip_vectorization=True),
        Property(name="typical_pattern", data_type=DataType.TEXT),  # Vectorized
        Property(name="related_failure_modes", data_type=DataType.TEXT_ARRAY,
                 skip_vectorization=True, filterable=True),
        Property(name="is_synthetic", data_type=DataType.BOOL,
                 skip_vectorization=True, filterable=True),
        Property(name="source", data_type=DataType.TEXT,
                 skip_vectorization=True),
        Property(name="balance_factors", data_type=DataType.TEXT_ARRAY,
                 skip_vectorization=True),
        Property(name="uit_balans_type", data_type=DataType.TEXT,
                 skip_vectorization=True, filterable=True),
        Property(name="affected_components", data_type=DataType.TEXT_ARRAY,
                 skip_vectorization=True, filterable=True),
    ]
)

# Load agent-generated JSONL
with open("features/telemetry_vsm/output/worldstate_snapshots.jsonl", "r") as f:
    data = [json.loads(line) for line in f if line.strip()]

print(f"Loaded {len(data)} WorldState snapshots from JSONL")

# Batch import
with collection.batch.fixed_size(batch_size=200) as batch:
    for i, item in enumerate(data):
        batch.add_object(item)
        
        if batch.number_errors > 10:
            print("Stopped due to excessive errors.")
            break

# Error handling
failed = collection.batch.failed_objects
if failed:
    print(f"Failed: {len(failed)}, First error: {failed[0]}")
else:
    print("All objects imported successfully!")

# Verify
total = collection.aggregate.over_all(total_count=True).total_count
print(f"Total objects in VSM_WorldStateSnapshot: {total}")

# Test queries
print(f"\nTesting queries:")
frozen_evap = collection.query.fetch_objects(
    filters=Filter.by_property("failure_mode").equal("ingevroren_verdamper"),
    limit=1
)
if frozen_evap.objects:
    print(f"  Frozen evaporator snapshot: {frozen_evap.objects[0].properties.get('snapshot_id', 'N/A')}")

synthetic = collection.query.fetch_objects(
    filters=Filter.by_property("is_synthetic").equal(True),
    limit=1
)
print(f"  Synthetic snapshots: {len(synthetic.objects)}")

client.close()
print("\n✅ VSM_WorldStateSnapshot upload complete!")

