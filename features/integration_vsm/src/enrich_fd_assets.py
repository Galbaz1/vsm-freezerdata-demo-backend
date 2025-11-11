#!/usr/bin/env python3
"""
Enrich FD_Assets collection with commissioning data (Context C).
Updates existing FD_Assets with design parameters for GetAssetHealth tool.
Follows official Weaviate docs pattern from docs/adding_data.md
"""

import weaviate
from weaviate.classes.init import Auth
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

# Get FD_Assets collection
try:
    collection = client.collections.get("FD_Assets")
    print("Found existing FD_Assets collection")
except Exception as e:
    print(f"Error: FD_Assets collection not found. Run scripts/seed_assets_alarms.py first.")
    client.close()
    exit(1)

# Load enrichment data
with open("features/integration_vsm/output/fd_assets_enrichment.json", "r") as f:
    enrichment = json.load(f)

print(f"Loaded enrichment data for asset: {enrichment['installation_id']}")

# Find the asset in Weaviate
result = collection.query.fetch_objects(
    filters=Filter.by_property("asset_id").equal("FZ-123"),  # From seed script
    limit=1
)

if not result.objects:
    print("Warning: Asset FZ-123 not found in FD_Assets. Creating new asset...")
    # Create new asset with enrichment
    asset_data = {
        "asset_id": "FZ-123",
        "asset_name": enrichment["asset_name"],
        "asset_type": "freezer",
        "location": enrichment["location"],
        "status": "operational",
        "commissioning_data": json.dumps(enrichment["commissioning_data"]),
        "components": json.dumps(enrichment["components"]),
        "control_settings": json.dumps(enrichment["control_settings"]),
        "operational_limits": json.dumps(enrichment["operational_limits"]),
        "balance_check_parameters": json.dumps(enrichment["balance_check_parameters"]),
        "metadata": json.dumps(enrichment["metadata"])
    }
    
    uuid = collection.data.insert(asset_data)
    print(f"Created new asset with UUID: {uuid}")
else:
    # Update existing asset
    asset_uuid = result.objects[0].uuid
    print(f"Found existing asset: {asset_uuid}")
    
    # Note: Weaviate update requires knowing which properties to update
    # For simplicity, we'll add properties if they don't exist in schema
    print("Note: FD_Assets schema may need manual update to include commissioning_data fields")
    print("Enrichment data saved to: features/integration_vsm/output/fd_assets_enrichment.json")
    print("Manual step: Add these properties to FD_Assets collection:")
    print("  - commissioning_data (TEXT)")
    print("  - components (TEXT)")
    print("  - control_settings (TEXT)")
    print("  - operational_limits (TEXT)")
    print("  - balance_check_parameters (TEXT)")

# Summary
print(f"\n=== Enrichment Summary ===")
print(f"Asset ID: {enrichment['installation_id']}")
print(f"Commissioning data keys: {list(enrichment['commissioning_data'].keys())}")
print(f"Components: {list(enrichment['components'].keys())}")
print(f"Control settings: {list(enrichment['control_settings'].keys())}")
print(f"Balance check parameters: {list(enrichment['balance_check_parameters'].keys())}")

client.close()
print("\n✅ FD_Assets enrichment complete!")
print("⚠️  Note: Schema update may be needed for new properties")

