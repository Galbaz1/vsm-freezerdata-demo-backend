#!/usr/bin/env python3
"""
Upload VSM_ManualSections collection to Weaviate Cloud.
Follows official Weaviate docs pattern from docs/adding_data.md

Note: Test/exercise content is flagged with content_type="opgave" (9 sections).
Production queries should filter: content_type != "opgave"
This content is useful for prompt engineering but should be filterable.
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

# Delete existing collection if it exists
try:
    client.collections.delete("VSM_ManualSections")
    print("Deleted existing VSM_ManualSections collection")
except Exception as e:
    print(f"No existing collection to delete (or error: {e})")

# Create collection
collection = client.collections.create(
    name="VSM_ManualSections",
    description="Manual sections from cooling technology manuals, SMIDO-tagged with 4 P's classification",
    vector_config=[
        Configure.Vectors.text2vec_weaviate(
            name="default",
            source_properties=["title", "body_text", "image_descriptions"]
        )
    ],
    properties=[
        # Core identification
        Property(name="section_id", data_type=DataType.TEXT,
                 skip_vectorization=True, filterable=True),
        Property(name="manual_id", data_type=DataType.TEXT,
                 skip_vectorization=True, filterable=True),
        Property(name="manual_title", data_type=DataType.TEXT,
                 skip_vectorization=True),
        Property(name="chunk_ids", data_type=DataType.TEXT_ARRAY,
                 skip_vectorization=True),
        
        # Content (vectorized)
        Property(name="title", data_type=DataType.TEXT),
        Property(name="body_text", data_type=DataType.TEXT),
        Property(name="language", data_type=DataType.TEXT,
                 skip_vectorization=True, filterable=True),
        Property(name="page_start", data_type=DataType.INT,
                 skip_vectorization=True, filterable=True),
        Property(name="page_end", data_type=DataType.INT,
                 skip_vectorization=True, filterable=True),
        Property(name="page_range", data_type=DataType.TEXT,
                 skip_vectorization=True),
        
        # Classification - 4 P's!
        Property(name="smido_step", data_type=DataType.TEXT,
                 skip_vectorization=True, filterable=True),
        Property(name="smido_steps", data_type=DataType.TEXT_ARRAY,
                 skip_vectorization=True, filterable=True),
        Property(name="content_type", data_type=DataType.TEXT,
                 skip_vectorization=True, filterable=True),
        Property(name="failure_mode", data_type=DataType.TEXT,
                 skip_vectorization=True, filterable=True),
        Property(name="failure_modes", data_type=DataType.TEXT_ARRAY,
                 skip_vectorization=True, filterable=True),
        Property(name="component", data_type=DataType.TEXT,
                 skip_vectorization=True, filterable=True),
        Property(name="components", data_type=DataType.TEXT_ARRAY,
                 skip_vectorization=True, filterable=True),
        
        # Metadata
        Property(name="contains_images", data_type=DataType.BOOL,
                 skip_vectorization=True, filterable=True),
        Property(name="image_descriptions", data_type=DataType.TEXT_ARRAY),
        Property(name="contains_table", data_type=DataType.BOOL,
                 skip_vectorization=True, filterable=True),
        Property(name="is_case_study", data_type=DataType.BOOL,
                 skip_vectorization=True, filterable=True),
        Property(name="case_title", data_type=DataType.TEXT,
                 skip_vectorization=True),
        Property(name="difficulty_level", data_type=DataType.TEXT,
                 skip_vectorization=True, filterable=True),
        
        # Diagram linking
        Property(name="related_diagram_ids", data_type=DataType.TEXT_ARRAY,
                 skip_vectorization=True),
    ]
)

# Load agent-generated JSONL
with open("features/manuals_vsm/output/manual_sections_classified.jsonl", "r") as f:
    data = [json.loads(line) for line in f if line.strip()]

print(f"Loaded {len(data)} sections from JSONL")

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
print(f"Total objects in VSM_ManualSections: {total}")

# Test SMIDO query - 4 P's (excluding test content)
print(f"\nTesting SMIDO queries (4 P's) - excluding opgave content:")
for step in ["melding", "technisch", "power", "procesinstellingen", "procesparameters", "productinput"]:
    result = collection.query.fetch_objects(
        filters=Filter.by_property("smido_step").equal(step) & 
                Filter.by_property("content_type").not_equal("opgave"),
        limit=1
    )
    count = len(result.objects)
    if count > 0:
        print(f"  {step}: {count} sections (example: {result.objects[0].properties.get('title', 'N/A')[:50]})")

# Test opgave filtering
opgave_count = collection.query.fetch_objects(
    filters=Filter.by_property("content_type").equal("opgave"),
    limit=1
)
print(f"\nTest content (opgave) sections: {len(opgave_count.objects)} (filterable for production)")

client.close()
print("\n✅ VSM_ManualSections upload complete!")

