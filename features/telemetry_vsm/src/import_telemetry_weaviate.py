#!/usr/bin/env python3
"""
Upload VSM_TelemetryEvent collection to Weaviate Cloud.
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
    name="VSM_TelemetryEvent",
    description="Telemetry events representing 'uit balans' incidents (not just broken components)",
    vector_config=[
        Configure.Vectors.text2vec_weaviate(
            name="default",
            source_properties=["description_nl", "worldstate_summary"]
        )
    ],
    properties=[
        # Identification
        Property(name="event_id", data_type=DataType.TEXT,
                 skip_vectorization=True, filterable=True),
        Property(name="asset_id", data_type=DataType.TEXT,
                 skip_vectorization=True, filterable=True),
        Property(name="t_start", data_type=DataType.TEXT,
                 skip_vectorization=True, filterable=True),
        Property(name="t_end", data_type=DataType.TEXT,
                 skip_vectorization=True, filterable=True),
        Property(name="duration_minutes", data_type=DataType.NUMBER,
                 skip_vectorization=True, filterable=True),
        
        # Classification
        Property(name="failure_mode", data_type=DataType.TEXT,
                 skip_vectorization=True, filterable=True),
        Property(name="failure_modes", data_type=DataType.TEXT_ARRAY,
                 skip_vectorization=True, filterable=True),
        Property(name="affected_components", data_type=DataType.TEXT_ARRAY,
                 skip_vectorization=True, filterable=True),
        Property(name="severity", data_type=DataType.TEXT,
                 skip_vectorization=True, filterable=True),
        
        # WorldState aggregates
        Property(name="room_temp_min", data_type=DataType.NUMBER,
                 skip_vectorization=True),
        Property(name="room_temp_max", data_type=DataType.NUMBER,
                 skip_vectorization=True),
        Property(name="room_temp_mean", data_type=DataType.NUMBER,
                 skip_vectorization=True),
        Property(name="hot_gas_mean", data_type=DataType.NUMBER,
                 skip_vectorization=True),
        Property(name="suction_mean", data_type=DataType.NUMBER,
                 skip_vectorization=True),
        Property(name="liquid_mean", data_type=DataType.NUMBER,
                 skip_vectorization=True),
        Property(name="ambient_mean", data_type=DataType.NUMBER,
                 skip_vectorization=True),
        Property(name="room_temp_trend", data_type=DataType.NUMBER,
                 skip_vectorization=True),
        Property(name="door_open_ratio", data_type=DataType.NUMBER,
                 skip_vectorization=True),
        
        # Description (vectorized)
        Property(name="description_nl", data_type=DataType.TEXT),
        Property(name="worldstate_summary", data_type=DataType.TEXT),
        
        # File reference
        Property(name="parquet_path", data_type=DataType.TEXT,
                 skip_vectorization=True),
        Property(name="time_range_start", data_type=DataType.TEXT,
                 skip_vectorization=True),
        Property(name="time_range_end", data_type=DataType.TEXT,
                 skip_vectorization=True),
        
        # Cross-references
        Property(name="related_manual_sections", data_type=DataType.TEXT_ARRAY,
                 skip_vectorization=True),
        Property(name="related_vlog_cases", data_type=DataType.TEXT_ARRAY,
                 skip_vectorization=True),
        Property(name="related_diagrams", data_type=DataType.TEXT_ARRAY,
                 skip_vectorization=True),
    ]
)

# Load agent-generated JSONL
with open("features/telemetry_vsm/output/telemetry_events.jsonl", "r") as f:
    data = [json.loads(line) for line in f if line.strip()]

print(f"Loaded {len(data)} events from JSONL")

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
print(f"Total objects in VSM_TelemetryEvent: {total}")

# Test queries
print(f"\nTesting queries:")
critical = collection.query.fetch_objects(
    filters=Filter.by_property("severity").equal("critical"),
    limit=1
)
print(f"  Critical events: {len(critical.objects)}")

frozen = collection.query.fetch_objects(
    filters=Filter.by_property("failure_modes").contains_any(["ingevroren_verdamper"]),
    limit=1
)
print(f"  Frozen evaporator events: {len(frozen.objects)}")

client.close()
print("\n✅ VSM_TelemetryEvent upload complete!")

