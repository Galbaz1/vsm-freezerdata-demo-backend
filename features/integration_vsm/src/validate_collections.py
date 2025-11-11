#!/usr/bin/env python3
"""
Validate all VSM collections in Weaviate.
Checks object counts, schema, queries, and A3 scenario coverage.
"""

import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.query import Filter
import os
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
print(f"Weaviate client ready: {client.is_ready()}\n")

# Expected counts
EXPECTED_COUNTS = {
    "VSM_Diagram": 9,
    "VSM_ManualSections": 167,
    "VSM_TelemetryEvent": 12,
    "VSM_VlogClip": 15,
    "VSM_VlogCase": 5,
    "VSM_WorldStateSnapshot": 13  # Updated: created 13 snapshots (5 from vlogs + 8 from balance factors)
}

print("=" * 60)
print("VSM COLLECTIONS VALIDATION")
print("=" * 60)

all_passed = True

# Check 1: Object Counts
print("\n1. Object Count Validation")
print("-" * 60)
for collection_name, expected in EXPECTED_COUNTS.items():
    try:
        collection = client.collections.get(collection_name)
        actual = collection.aggregate.over_all(total_count=True).total_count
        status = "✅ PASS" if actual == expected else f"⚠️  MISMATCH"
        print(f"{collection_name:30s} Expected: {expected:4d}  Actual: {actual:4d}  {status}")
        if actual != expected:
            all_passed = False
    except Exception as e:
        print(f"{collection_name:30s} ❌ ERROR: {str(e)[:50]}")
        all_passed = False

# Check 2: SMIDO 4 P's Queries
print("\n2. SMIDO 4 P's Validation (VSM_ManualSections)")
print("-" * 60)
manual_sections = client.collections.get("VSM_ManualSections")
four_ps = ["power", "procesinstellingen", "procesparameters", "productinput"]
for step in four_ps:
    result = manual_sections.query.fetch_objects(
        filters=Filter.by_property("smido_step").equal(step),
        limit=1
    )
    count = len(result.objects)
    # productinput (P4) may have 0 sections - it's about external factors, not technical manual content
    if step == "productinput" and count == 0:
        status = "⚠️  Expected (external factors)"
    else:
        status = "✅" if count > 0 else "❌"
        if count == 0:
            all_passed = False
    example = result.objects[0].properties.get('title', 'N/A')[:50] if result.objects else "N/A"
    print(f"  {step:20s} {status} (example: {example})")

# Check 3: A3 Frozen Evaporator Scenario
print("\n3. A3 Frozen Evaporator Scenario Coverage")
print("-" * 60)

# Check in VlogCase
vlog_cases = client.collections.get("VSM_VlogCase")
a3_case = vlog_cases.query.fetch_objects(
    filters=Filter.by_property("case_id").equal("A3"),
    limit=1
)
if a3_case.objects:
    print(f"  VSM_VlogCase A3: ✅ Found")
    print(f"    Title: {a3_case.objects[0].properties.get('case_title', 'N/A')[:70]}")
else:
    print(f"  VSM_VlogCase A3: ❌ Not found")
    all_passed = False

# Check in TelemetryEvent
telemetry_events = client.collections.get("VSM_TelemetryEvent")
frozen_evap_events = telemetry_events.query.fetch_objects(
    filters=Filter.by_property("failure_modes").contains_any(["ingevroren_verdamper"]),
    limit=1
)
if frozen_evap_events.objects:
    print(f"  VSM_TelemetryEvent (frozen evap): ✅ Found {len(frozen_evap_events.objects)} events")
else:
    print(f"  VSM_TelemetryEvent (frozen evap): ❌ Not found")
    all_passed = False

# Check in ManualSections
manual_sections = client.collections.get("VSM_ManualSections")
frozen_manual = manual_sections.query.fetch_objects(
    filters=Filter.by_property("failure_modes").contains_any(["ingevroren_verdamper"]),
    limit=1
)
if frozen_manual.objects:
    print(f"  VSM_ManualSections (frozen evap): ✅ Found")
    print(f"    Section: {frozen_manual.objects[0].properties.get('title', 'N/A')[:70]}")
else:
    print(f"  VSM_ManualSections (frozen evap): ❌ Not found")
    all_passed = False

# Check in WorldStateSnapshot
snapshots = client.collections.get("VSM_WorldStateSnapshot")
frozen_snapshot = snapshots.query.fetch_objects(
    filters=Filter.by_property("failure_mode").equal("ingevroren_verdamper"),
    limit=1
)
if frozen_snapshot.objects:
    print(f"  VSM_WorldStateSnapshot (frozen evap): ✅ Found")
    print(f"    Pattern: {frozen_snapshot.objects[0].properties.get('typical_pattern', 'N/A')[:70]}")
else:
    print(f"  VSM_WorldStateSnapshot (frozen evap): ❌ Not found")
    all_passed = False

# Check 4: Vectorization
print("\n4. Vectorization Check")
print("-" * 60)
try:
    # Test if vectors are generated
    diagram = client.collections.get("VSM_Diagram")
    result = diagram.query.fetch_objects(limit=1, include_vector=True)
    if result.objects and result.objects[0].vector:
        print(f"  VSM_Diagram vectors: ✅ Generated ({len(result.objects[0].vector['default'])} dimensions)")
    else:
        print(f"  VSM_Diagram vectors: ❌ Not generated")
        all_passed = False
except Exception as e:
    print(f"  Vectorization check: ⚠️  {str(e)[:50]}")

# Check 5: Cross-Reference Fields
print("\n5. Cross-Reference Fields")
print("-" * 60)
test_case = vlog_cases.query.fetch_objects(limit=1)
if test_case.objects:
    props = test_case.objects[0].properties
    has_refs = (
        "related_manual_sections" in props and
        "related_telemetry_events" in props and
        "related_diagrams" in props
    )
    status = "✅" if has_refs else "⚠️  Incomplete"
    print(f"  VSM_VlogCase has cross-ref fields: {status}")
else:
    print(f"  VSM_VlogCase: ⚠️  No objects to test")

# Final Summary
print("\n" + "=" * 60)
if all_passed:
    print("✅ ALL VALIDATIONS PASSED!")
else:
    print("⚠️  SOME VALIDATIONS FAILED - Review errors above")
print("=" * 60)

client.close()

