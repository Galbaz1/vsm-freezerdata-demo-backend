#!/usr/bin/env python3
"""
Upload VSM_VlogClip and VSM_VlogCase collections to Weaviate Cloud.
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

# ========== VSM_VlogClip Collection ==========
print("\n=== Creating VSM_VlogClip collection ===")
collection_clips = client.collections.create(
    name="VSM_VlogClip",
    description="Individual video clips showing troubleshooting steps (15 clips from 5 cases)",
    vector_config=[
        Configure.Vectors.text2vec_weaviate(
            name="default",
            source_properties=["title", "problem_summary", "root_cause", "solution_summary", "steps_text", "world_state_pattern"]
        )
    ],
    properties=[
        # Identification
        Property(name="clip_id", data_type=DataType.TEXT,
                 skip_vectorization=True, filterable=True),
        Property(name="case_id", data_type=DataType.TEXT,
                 skip_vectorization=True, filterable=True),
        Property(name="clip_number", data_type=DataType.INT,
                 skip_vectorization=True, filterable=True),
        Property(name="video_filename", data_type=DataType.TEXT,
                 skip_vectorization=True),
        Property(name="video_path", data_type=DataType.TEXT,
                 skip_vectorization=True),
        Property(name="duration_seconds", data_type=DataType.NUMBER,
                 skip_vectorization=True),
        
        # Content (vectorized)
        Property(name="title", data_type=DataType.TEXT),
        Property(name="language", data_type=DataType.TEXT,
                 skip_vectorization=True, filterable=True),
        Property(name="problem_summary", data_type=DataType.TEXT),
        Property(name="root_cause", data_type=DataType.TEXT),
        Property(name="solution_summary", data_type=DataType.TEXT),
        Property(name="steps_text", data_type=DataType.TEXT),
        
        # Classification
        Property(name="smido_step_primary", data_type=DataType.TEXT,
                 skip_vectorization=True, filterable=True),
        Property(name="smido_steps", data_type=DataType.TEXT_ARRAY,
                 skip_vectorization=True, filterable=True),
        Property(name="failure_mode", data_type=DataType.TEXT,
                 skip_vectorization=True, filterable=True),
        Property(name="failure_modes", data_type=DataType.TEXT_ARRAY,
                 skip_vectorization=True, filterable=True),
        Property(name="component_primary", data_type=DataType.TEXT,
                 skip_vectorization=True, filterable=True),
        Property(name="components", data_type=DataType.TEXT_ARRAY,
                 skip_vectorization=True, filterable=True),
        
        # Sensor correlation (vectorized)
        Property(name="world_state_pattern", data_type=DataType.TEXT),
        
        # Tags
        Property(name="tags", data_type=DataType.TEXT_ARRAY,
                 skip_vectorization=True, filterable=True),
        Property(name="skill_level", data_type=DataType.TEXT,
                 skip_vectorization=True, filterable=True),
        Property(name="is_complete_case", data_type=DataType.BOOL,
                 skip_vectorization=True, filterable=True),
    ]
)

# Load clips
with open("features/vlogs_vsm/output/vlog_clips_enriched.jsonl", "r") as f:
    clips_data = [json.loads(line) for line in f if line.strip()]

print(f"Loaded {len(clips_data)} clips from JSONL")

# Import clips
with collection_clips.batch.fixed_size(batch_size=200) as batch:
    for i, item in enumerate(clips_data):
        batch.add_object(item)
        
        if batch.number_errors > 10:
            print("Stopped due to excessive errors.")
            break

failed = collection_clips.batch.failed_objects
if failed:
    print(f"Failed: {len(failed)}, First error: {failed[0]}")
else:
    print("All clip objects imported successfully!")

total_clips = collection_clips.aggregate.over_all(total_count=True).total_count
print(f"Total objects in VSM_VlogClip: {total_clips}")

# ========== VSM_VlogCase Collection ==========
print("\n=== Creating VSM_VlogCase collection ===")
collection_cases = client.collections.create(
    name="VSM_VlogCase",
    description="Aggregated video cases (A1-A5) with complete problem-solution workflows",
    vector_config=[
        Configure.Vectors.text2vec_weaviate(
            name="default",
            source_properties=["case_title", "problem_summary", "root_cause", "solution_summary", "transcript_nl", "world_state_pattern"]
        )
    ],
    properties=[
        # Identification
        Property(name="case_id", data_type=DataType.TEXT,
                 skip_vectorization=True, filterable=True),
        Property(name="case_title", data_type=DataType.TEXT),
        Property(name="clip_ids", data_type=DataType.TEXT_ARRAY,
                 skip_vectorization=True),
        
        # Content (vectorized)
        Property(name="problem_summary", data_type=DataType.TEXT),
        Property(name="root_cause", data_type=DataType.TEXT),
        Property(name="solution_summary", data_type=DataType.TEXT),
        Property(name="transcript_nl", data_type=DataType.TEXT),
        
        # Classification
        Property(name="smido_step_primary", data_type=DataType.TEXT,
                 skip_vectorization=True, filterable=True),
        Property(name="smido_steps", data_type=DataType.TEXT_ARRAY,
                 skip_vectorization=True, filterable=True),
        Property(name="failure_mode", data_type=DataType.TEXT,
                 skip_vectorization=True, filterable=True),
        Property(name="failure_modes", data_type=DataType.TEXT_ARRAY,
                 skip_vectorization=True, filterable=True),
        Property(name="component_primary", data_type=DataType.TEXT,
                 skip_vectorization=True, filterable=True),
        Property(name="components", data_type=DataType.TEXT_ARRAY,
                 skip_vectorization=True, filterable=True),
        
        # Sensor correlation (vectorized)
        Property(name="world_state_pattern", data_type=DataType.TEXT),
        Property(name="typical_sensor_conditions", data_type=DataType.TEXT,
                 skip_vectorization=True),
        
        # Cross-references
        Property(name="related_manual_sections", data_type=DataType.TEXT_ARRAY,
                 skip_vectorization=True),
        Property(name="related_telemetry_events", data_type=DataType.TEXT_ARRAY,
                 skip_vectorization=True),
        Property(name="related_diagrams", data_type=DataType.TEXT_ARRAY,
                 skip_vectorization=True),
    ]
)

# Load cases
with open("features/vlogs_vsm/output/vlog_cases_enriched.jsonl", "r") as f:
    cases_data = [json.loads(line) for line in f if line.strip()]

print(f"Loaded {len(cases_data)} cases from JSONL")

# Import cases
with collection_cases.batch.fixed_size(batch_size=200) as batch:
    for i, item in enumerate(cases_data):
        batch.add_object(item)
        
        if batch.number_errors > 10:
            print("Stopped due to excessive errors.")
            break

failed = collection_cases.batch.failed_objects
if failed:
    print(f"Failed: {len(failed)}, First error: {failed[0]}")
else:
    print("All case objects imported successfully!")

total_cases = collection_cases.aggregate.over_all(total_count=True).total_count
print(f"Total objects in VSM_VlogCase: {total_cases}")

# Test A3 case query
print(f"\nTesting A3 (frozen evaporator) case query:")
result = collection_cases.query.fetch_objects(
    filters=Filter.by_property("case_id").equal("A3"),
    limit=1
)
if result.objects:
    print(f"  Found A3 case: {result.objects[0].properties.get('case_title', 'N/A')[:80]}")

client.close()
print("\n✅ VSM_VlogClip and VSM_VlogCase upload complete!")

