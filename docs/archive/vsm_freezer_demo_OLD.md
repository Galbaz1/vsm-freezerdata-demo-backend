# VSM FreezerData Demo Implementation Guide

This document provides comprehensive guidance for implementing the Virtual Service Mechanic (VSM) demonstration—a domain-specific service assistant built on the Elysia platform. The goal is to create an agent that answers health-check questions, detects faults, and guides users through diagnosis and remediation for industrial freezer assets.

---

## Table of Contents

- [Overview](#overview)
- [Objectives](#objectives)
- [Data Assets](#data-assets)
- [Weaviate Collections](#weaviate-collections)
- [Custom Tools](#custom-tools)
- [Decision Tree Architecture](#decision-tree-architecture)
- [Implementation Steps](#implementation-steps)
- [Example Queries](#example-queries)
- [Testing Strategy](#testing-strategy)
- [Development Tips](#development-tips)

---

## Overview

The VSM FreezerData demo showcases how Elysia can be adapted to create a specialized service assistant that:

1. **Monitors asset health** by analyzing real telemetry data
2. **Detects and explains faults** using sensor patterns and documentation
3. **Guides diagnostics** through structured workflows
4. **Generates service notes** documenting troubleshooting actions

Unlike a general-purpose chatbot, this demo uses Elysia's decision tree architecture to provide predictable, auditable diagnostic paths.

---

## Objectives

### 1. Health Assessment
**User Query:** "How is machine FZ-123 doing?"

**Agent Actions:**
- Fetch recent telemetry window (e.g., last 24 hours)
- Check for active alarms
- Summarize asset state (normal, warning, critical)
- List alarm codes with severity and impact

**Output Example:**
```
Asset FZ-123 Status: ⚠️ WARNING

Current State:
- Main freezer: -28.5°C (target: -33°C)
- Hot gas line: 62°C (normal: 45-55°C)
- Battery: 98%

Active Alarms:
- E102: High temperature deviation (WARNING)
- E305: Fan RPM signal loss (CRITICAL)

Impact: Reduced cooling efficiency, potential product loss
```

### 2. Fault Explanation
**User Query:** "Explain the fan fault alarm on FZ-123"

**Agent Actions:**
- Retrieve alarm details (code E305, timestamp)
- Fetch telemetry around fault occurrence
- Search manuals for alarm code documentation
- Query past cases with similar symptoms

**Output Example:**
```
Alarm E305: Evaporator Fan RPM Signal Loss

Description:
The fan speed sensor is not reporting RPM data. This indicates either:
1. Sensor wire disconnection
2. Fan motor bearing failure
3. Control board communication error

Telemetry Evidence:
- Fan RPM: flat at 0 (expected: 1200-1400)
- Temperature: rising +0.5°C/hour since 14:30
- Hot gas temp: elevated to 62°C (+12°C above normal)

See: Manual Section 4.2.3 "Evaporator Fan Diagnostics" (page 45)
```

### 3. Cause Analysis
**User Query:** "What could cause this fan issue?"

**Agent Actions:**
- Analyze sensor patterns for correlation
- Search documentation for diagnostic procedures
- Retrieve similar past incidents
- Generate ranked hypothesis list

**Output Example:**
```
Root Cause Analysis - E305 Fan Fault

Likely Causes (ranked by probability):

1. Fan Wire Disconnection (45%)
   Evidence: RPM signal flat at 0, sudden onset
   Manual Ref: Section 4.2.3
   Next Step: Visual inspection of fan wiring harness

2. Fan Motor Bearing Seizure (30%)
   Evidence: Temperature rising, hot gas elevated
   Past Cases: 3 similar incidents in last year
   Next Step: Manually rotate fan blade, check for resistance

3. Control Board Failure (20%)
   Evidence: No other sensor anomalies
   Manual Ref: Section 5.1.2
   Next Step: Test board output voltage (should be 12V DC)

4. Sensor Module Defect (5%)
   Evidence: Low probability based on pattern
   Next Step: Swap sensor with spare to isolate

Diagnostic Checklist:
□ Check wire connections at fan terminal block
□ Verify 12V power supply at fan motor
□ Manually spin fan blade (should rotate freely)
□ Test RPM sensor output with multimeter
□ Review control board error logs
```

---

## Data Assets

### Telemetry Data
**Location:** `features/telemetry/timeseries_freezerdata/`

**Files:**
- `135_1570_cleaned.parquet` - Production-ready telemetry (785K records, 528 days)
- `135_1570_cleaned_with_flags.parquet` - Audit trail with outlier flags

**Sensors (9 variables):**
- `sGekoeldeRuimte` - Main freezer temperature (°C)
- `p:42_s:_a:standard_n:Gekoelderuimte(2)_inactive` - Secondary freezer (°C)
- `sHeetgasLeiding` - Hot gas line temperature (°C)
- `sVloeistofleiding` - Liquid line temperature (°C)
- `sZuigleiding` - Suction line temperature (°C)
- `sOmgeving` - Ambient temperature (°C)
- `sDeurcontact` - Door contact sensor (0/1)
- `sRSSI` - Signal strength (dBm)
- `sBattery` - Battery level (%)

**Documentation:** See [docs/eda/README.md](eda/README.md) for comprehensive data analysis.

### Technical Manuals
**Location:** `features/extraction/production_output/`

**Processed Manuals:**
1. `koelinstallaties-opbouw-en-werking_theorie/` - Refrigeration construction & operation
2. `koelinstallaties-inspectie-en-onderhoud_theorie/` - Inspection & maintenance
3. `storingzoeken-koeltechniek_theorie/` - Troubleshooting guide

**Output Artifacts:**
- `*.text_chunks.jsonl` - Text/table chunks with embeddings
- `*.visual_chunks.jsonl` - Diagrams and figures
- `*.pages.jsonl` - Page-level context
- `*.meta.json` - Document metadata

See [features/extraction/README.md](../features/extraction/README.md) for pipeline details.

---

## Weaviate Collections

Create the following collections for the VSM demo:

### 1. FD_Assets
**Purpose:** Asset inventory and metadata

**Schema:**
```python
from weaviate.classes.config import Configure, Property, DataType

client.collections.create(
    name="FD_Assets",
    vectorizer_config=Configure.Vectorizer.text2vec_weaviate(),
    properties=[
        Property(name="asset_id", data_type=DataType.TEXT),
        Property(name="model", data_type=DataType.TEXT),
        Property(name="location", data_type=DataType.TEXT),
        Property(name="installation_date", data_type=DataType.DATE),
        Property(name="capacity_liters", data_type=DataType.NUMBER),
        Property(name="target_temp", data_type=DataType.NUMBER),
        Property(name="status", data_type=DataType.TEXT),  # active, maintenance, offline
    ]
)
```

**Example Data:**
```json
{
  "asset_id": "FZ-123",
  "model": "Industrial Freezer 135-1570",
  "location": "Warehouse A, Bay 3",
  "installation_date": "2022-10-15",
  "capacity_liters": 1500,
  "target_temp": -33.0,
  "status": "active"
}
```

### 2. FD_Telemetry
**Purpose:** Time-series sensor data

**Schema:**
```python
client.collections.create(
    name="FD_Telemetry",
    vectorizer_config=Configure.Vectorizer.none(),  # No vectorization for time series
    properties=[
        Property(name="asset_id", data_type=DataType.TEXT),
        Property(name="timestamp", data_type=DataType.DATE),
        Property(name="main_temp", data_type=DataType.NUMBER),
        Property(name="secondary_temp", data_type=DataType.NUMBER),
        Property(name="hot_gas_temp", data_type=DataType.NUMBER),
        Property(name="liquid_temp", data_type=DataType.NUMBER),
        Property(name="suction_temp", data_type=DataType.NUMBER),
        Property(name="ambient_temp", data_type=DataType.NUMBER),
        Property(name="door_open", data_type=DataType.BOOL),
        Property(name="signal_strength", data_type=DataType.NUMBER),
        Property(name="battery_level", data_type=DataType.NUMBER),
    ]
)
```

**Import Script:**
```python
import pandas as pd
from datetime import datetime

df = pd.read_parquet('features/telemetry/timeseries_freezerdata/135_1570_cleaned.parquet')
df['asset_id'] = 'FZ-123'  # Add asset identifier

with collection.batch.fixed_size(batch_size=1000) as batch:
    for idx, row in df.iterrows():
        batch.add_object({
            "asset_id": "FZ-123",
            "timestamp": idx.isoformat(),
            "main_temp": row['sGekoeldeRuimte'],
            "secondary_temp": row['p:42_s:_a:standard_n:Gekoelderuimte(2)_inactive'],
            "hot_gas_temp": row['sHeetgasLeiding'],
            "liquid_temp": row['sVloeistofleiding'],
            "suction_temp": row['sZuigleiding'],
            "ambient_temp": row['sOmgeving'],
            "door_open": bool(row['sDeurcontact']),
            "signal_strength": row['sRSSI'],
            "battery_level": row['sBattery'],
        })
```

### 3. FD_Alarms
**Purpose:** Alarm events and codes

**Schema:**
```python
client.collections.create(
    name="FD_Alarms",
    vectorizer_config=Configure.Vectorizer.text2vec_weaviate(),
    properties=[
        Property(name="asset_id", data_type=DataType.TEXT),
        Property(name="timestamp", data_type=DataType.DATE),
        Property(name="alarm_code", data_type=DataType.TEXT),
        Property(name="severity", data_type=DataType.TEXT),  # info, warning, critical
        Property(name="message", data_type=DataType.TEXT),
        Property(name="acknowledged", data_type=DataType.BOOL),
        Property(name="resolved_at", data_type=DataType.DATE),
    ]
)
```

**Sample Alarms:**
```python
# Synthetic alarm data for demo
alarms = [
    {
        "asset_id": "FZ-123",
        "timestamp": "2024-03-15T14:30:00Z",
        "alarm_code": "E305",
        "severity": "critical",
        "message": "Evaporator fan RPM signal loss",
        "acknowledged": False,
        "resolved_at": None
    },
    {
        "asset_id": "FZ-123",
        "timestamp": "2024-03-15T14:35:00Z",
        "alarm_code": "E102",
        "severity": "warning",
        "message": "High temperature deviation from setpoint",
        "acknowledged": False,
        "resolved_at": None
    }
]
```

### 4. FD_Documents
**Purpose:** Manual chunks for semantic search

**Schema:**
```python
client.collections.create(
    name="FD_Documents",
    vectorizer_config=Configure.Vectorizer.text2vec_weaviate(),
    properties=[
        Property(name="doc_id", data_type=DataType.TEXT),
        Property(name="title", data_type=DataType.TEXT),
        Property(name="asset_model", data_type=DataType.TEXT),
        Property(name="section_title", data_type=DataType.TEXT),
        Property(name="content", data_type=DataType.TEXT),
        Property(name="page", data_type=DataType.NUMBER),
        Property(name="chunk_type", data_type=DataType.TEXT),  # text, table, figure
        Property(name="language", data_type=DataType.TEXT),  # nl, en
    ]
)
```

**Import from Extraction Pipeline:**
```python
import json

# Load text chunks
with open('features/extraction/production_output/storingzoeken-koeltechniek_theorie/storingzoeken-koeltechniek_theorie.text_chunks.jsonl') as f:
    for line in f:
        chunk = json.loads(line)
        collection.data.insert({
            "doc_id": "troubleshooting_manual",
            "title": "Refrigeration Troubleshooting",
            "asset_model": "135-1570",
            "section_title": "Section extracted from PDF",
            "content": chunk['markdown'],
            "page": chunk['page'],
            "chunk_type": chunk['chunk_type'],
            "language": chunk.get('language', 'nl')
        })
```

### 5. FD_Cases (Optional)
**Purpose:** Past incident records

**Schema:**
```python
client.collections.create(
    name="FD_Cases",
    vectorizer_config=Configure.Vectorizer.text2vec_weaviate(),
    properties=[
        Property(name="case_id", data_type=DataType.TEXT),
        Property(name="asset_id", data_type=DataType.TEXT),
        Property(name="symptom", data_type=DataType.TEXT),
        Property(name="root_cause", data_type=DataType.TEXT),
        Property(name="actions_taken", data_type=DataType.TEXT),
        Property(name="outcome", data_type=DataType.TEXT),
        Property(name="created_at", data_type=DataType.DATE),
        Property(name="technician", data_type=DataType.TEXT),
    ]
)
```

---

## Custom Tools

Implement these tools in `elysia/tools/vsm/`:

### 1. GetAssetHealth
**File:** `elysia/tools/vsm/health.py`

```python
from elysia.objects import Tool, Result, Status
from datetime import datetime, timedelta

class GetAssetHealth(Tool):
    """Summarize recent telemetry and alarms for an asset."""

    def __init__(self):
        self.name = "Get Asset Health"
        self.description = "Fetch health status, recent telemetry, and active alarms"

    async def __call__(self, tree_data, asset_id: str):
        yield Status(message=f"Checking health for {asset_id}...")

        # Fetch recent telemetry (last 24 hours)
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)

        # Query FD_Telemetry collection
        telemetry_query = tree_data.collections['FD_Telemetry'].query.fetch_objects(
            filters=tree_data.filters.by_property("asset_id").equal(asset_id),
            limit=1440  # 1 per minute for 24 hours
        )

        # Query FD_Alarms for active alarms
        alarms_query = tree_data.collections['FD_Alarms'].query.fetch_objects(
            filters=(
                tree_data.filters.by_property("asset_id").equal(asset_id) &
                tree_data.filters.by_property("acknowledged").equal(False)
            )
        )

        # Compute statistics and format response
        health_summary = self._compute_health_summary(telemetry_query, alarms_query)

        # Store in environment for subsequent tools
        tree_data.environment.set("current_asset_health", health_summary)

        yield Result(objects=[health_summary])

    def _compute_health_summary(self, telemetry, alarms):
        # Implementation details...
        pass
```

### 2. GetTelemetryWindow
**File:** `elysia/tools/vsm/telemetry.py`

```python
class GetTelemetryWindow(Tool):
    """Return structured summary of sensor readings in a time window."""

    async def __call__(self, tree_data, asset_id: str, center_time: datetime, window_minutes: int = 60):
        yield Status(message=f"Analyzing {window_minutes}-minute window around {center_time}...")

        # Calculate window bounds
        start = center_time - timedelta(minutes=window_minutes//2)
        end = center_time + timedelta(minutes=window_minutes//2)

        # Query telemetry
        # ... implementation

        # Compute trends, anomalies, statistics
        window_summary = {
            "time_range": {"start": start.isoformat(), "end": end.isoformat()},
            "main_temp": {"mean": -32.5, "min": -35, "max": -28, "trend": "rising"},
            "hot_gas_temp": {"mean": 62, "min": 60, "max": 65, "trend": "stable"},
            "anomalies": ["Fan RPM flat at 0 (expected 1200-1400 RPM)"]
        }

        tree_data.environment.set("telemetry_window", window_summary)
        yield Result(objects=[window_summary])
```

### 3. SearchDocuments
**File:** `elysia/tools/vsm/search_docs.py`

```python
class SearchDocuments(Tool):
    """Semantic search over FD_Documents collection."""

    async def __call__(self, tree_data, query: str, filters: dict = None):
        yield Status(message=f"Searching manuals for: {query}")

        # Build Weaviate query
        search_results = tree_data.collections['FD_Documents'].query.near_text(
            query=query,
            limit=5,
            return_properties=["title", "section_title", "content", "page"]
        )

        # Format results with citations
        formatted_results = []
        for obj in search_results.objects:
            formatted_results.append({
                "content": obj.properties['content'],
                "citation": f"{obj.properties['title']} - {obj.properties['section_title']} (p. {obj.properties['page']})"
            })

        yield Result(objects=formatted_results)
```

### 4. GetAlarms
**File:** `elysia/tools/vsm/alarms.py`

```python
class GetAlarms(Tool):
    """List alarms for an asset within a time period."""

    async def __call__(self, tree_data, asset_id: str, since: datetime = None):
        if since is None:
            since = datetime.now() - timedelta(days=7)

        yield Status(message=f"Fetching alarms since {since.strftime('%Y-%m-%d')}...")

        # Query FD_Alarms
        # ... implementation

        yield Result(objects=alarm_list)
```

---

## Decision Tree Architecture

### Node Structure

Create a custom tree with specialized decision nodes:

```python
from elysia import Tree
from elysia.tree.util import DecisionNode

# Initialize empty tree
tree = Tree(initialization_mode="empty", debug=True)

# Define decision nodes
health_check_node = DecisionNode(
    name="HealthCheck",
    description="Check asset health status",
    available_tools=[GetAssetHealth, GetAlarms],
    completion_criteria=lambda env: "current_asset_health" in env
)

explain_error_node = DecisionNode(
    name="ExplainError",
    description="Explain a specific alarm code",
    available_tools=[GetTelemetryWindow, SearchDocuments],
    completion_criteria=lambda env: "error_explanation" in env
)

cause_analysis_node = DecisionNode(
    name="CauseAnalysis",
    description="Analyze root causes and suggest diagnostics",
    available_tools=[SearchDocuments, SearchCases],
    completion_criteria=lambda env: "hypothesis_list" in env
)

# Add nodes to tree
tree.add_node(health_check_node, parent="root")
tree.add_node(explain_error_node, parent="root")
tree.add_node(cause_analysis_node, parent="root")
```

### Routing Logic

The LLM decides which branch to take based on the user query:

- **Health check queries** → `HealthCheckNode`
- **Alarm explanation queries** → `ExplainErrorNode`
- **Diagnostic/cause queries** → `CauseAnalysisNode`

---

## Implementation Steps

### Step 1: Prepare Data Collections

```bash
# 1. Load telemetry into Weaviate
python scripts/load_telemetry.py

# 2. Import manual chunks
python scripts/load_documents.py

# 3. Create synthetic alarms for demo
python scripts/create_sample_alarms.py

# 4. Preprocess collections
python -c "from elysia.preprocessing.collection import preprocess; \
           preprocess(collection_names=['FD_Assets', 'FD_Telemetry', 'FD_Alarms', 'FD_Documents'])"
```

### Step 2: Implement Custom Tools

Create tool files in `elysia/tools/vsm/`:
- `health.py` - GetAssetHealth
- `telemetry.py` - GetTelemetryWindow
- `alarms.py` - GetAlarms
- `search_docs.py` - SearchDocuments

### Step 3: Build Decision Tree

Create `vsm_tree.py`:

```python
from elysia import Tree
from elysia.tools.vsm import GetAssetHealth, GetTelemetryWindow, SearchDocuments, GetAlarms

tree = Tree(initialization_mode="one_branch")

# Register VSM tools
tree.add_tool(GetAssetHealth, branch_id="base")
tree.add_tool(GetTelemetryWindow, branch_id="base")
tree.add_tool(GetAlarms, branch_id="base")
tree.add_tool(SearchDocuments, branch_id="base")

# Save configuration
tree.save("vsm_freezer_config.json")
```

### Step 4: Test with Sample Queries

```python
# Load tree
tree = Tree.load("vsm_freezer_config.json")

# Test health check
response = tree("How is FZ-123 doing?")
print(response)

# Test alarm explanation
response = tree("Explain the fan fault alarm on FZ-123")
print(response)
```

### Step 5: Create Service Note Generator

Add a final tool that formats the conversation into a structured service note:

```python
class GenerateServiceNote(Tool):
    async def __call__(self, tree_data):
        # Extract from environment
        health = tree_data.environment.get("current_asset_health")
        actions = tree_data.environment.get("user_actions")

        note = f"""
SERVICE NOTE - {datetime.now().strftime('%Y-%m-%d')}
Asset: {health['asset_id']}
Technician: {tree_data.user_id}

SYMPTOMS:
{health['active_alarms']}

ROOT CAUSE:
{tree_data.environment.get('confirmed_cause')}

ACTIONS TAKEN:
{actions}

OUTCOME:
{tree_data.environment.get('resolution_status')}
"""

        # Store in FD_Cases
        # ... implementation

        yield Result(objects=[{"service_note": note}])
```

---

## Example Queries

### Query 1: Initial Health Check
```
User: "Check the status of freezer FZ-123"

Agent:
→ Calls GetAssetHealth(asset_id="FZ-123")
→ Calls GetAlarms(asset_id="FZ-123")
→ Returns health summary with active alarms
```

### Query 2: Alarm Investigation
```
User: "Why is the temperature rising on FZ-123?"

Agent:
→ Checks environment for existing health data
→ Calls GetTelemetryWindow(center_time=<alarm_time>, window_minutes=120)
→ Identifies fan RPM anomaly
→ Calls SearchDocuments(query="fan RPM loss high temperature")
→ Returns explanation with manual references
```

### Query 3: Root Cause Analysis
```
User: "What could cause the fan to stop?"

Agent:
→ Calls SearchDocuments(query="evaporator fan failure causes")
→ Calls SearchCases(query="fan RPM signal loss")
→ Synthesizes hypothesis list with probabilities
→ Suggests diagnostic checklist
```

### Query 4: Guided Diagnosis
```
User: "I checked the wiring and it looks fine"

Agent:
→ Updates environment with user feedback
→ Adjusts hypothesis probabilities
→ Calls SearchDocuments(query="fan motor bearing test")
→ Suggests next diagnostic step
```

### Query 5: Resolution Documentation
```
User: "I replaced the fan motor and temperature is back to normal"

Agent:
→ Calls GenerateServiceNote()
→ Stores case in FD_Cases
→ Confirms resolution
```

---

## Testing Strategy

### Unit Tests
Create `tests/vsm_freezer/test_tools.py`:

```python
import pytest
from elysia.tools.vsm import GetAssetHealth

@pytest.mark.asyncio
async def test_get_asset_health():
    # Mock tree_data
    tree_data = MockTreeData()

    # Call tool
    tool = GetAssetHealth()
    results = [r async for r in tool(tree_data, asset_id="FZ-123")]

    # Assert
    assert len(results) == 2  # Status + Result
    assert results[1].objects[0]['asset_id'] == "FZ-123"
```

### Integration Tests
Create realistic scenarios with mock data:

```python
@pytest.mark.asyncio
async def test_full_diagnostic_workflow():
    tree = Tree.load("vsm_freezer_config.json")

    # Simulate fault scenario
    response1 = tree("Check FZ-123")
    assert "E305" in response1

    # Follow-up
    response2 = tree("Explain alarm E305")
    assert "fan" in response2.lower()

    # Diagnosis
    response3 = tree("What could cause this?")
    assert len(response3.hypotheses) >= 3
```

### Demo Script
Create `scripts/run_demo.py`:

```python
from elysia import Tree

tree = Tree.load("vsm_freezer_config.json")

# Scenario 1: Normal operation
print("=== Scenario 1: Health Check ===")
print(tree("How is FZ-123?"))

# Scenario 2: Active alarm
print("\n=== Scenario 2: Fault Investigation ===")
print(tree("There's a high temperature alarm on FZ-123"))
print(tree("What does alarm E102 mean?"))
print(tree("What should I check?"))

# Scenario 3: Root cause found
print("\n=== Scenario 3: Resolution ===")
print(tree("The fan motor was seized. I replaced it."))
print(tree("Generate a service note"))
```

---

## Development Tips

### 1. Use Debug Mode
```python
tree = Tree(debug=True)
```
This enables verbose logging to track decision paths.

### 2. Test with Synthetic Alarms
Create controlled fault scenarios:

```python
# Inject test alarm
test_alarm = {
    "asset_id": "FZ-123",
    "timestamp": datetime.now().isoformat(),
    "alarm_code": "E305",
    "severity": "critical",
    "message": "Fan RPM signal loss"
}

collection.data.insert(test_alarm)
```

### 3. Validate Telemetry Queries
Before full integration, test Weaviate queries directly:

```python
from elysia.util.client import ClientManager

with ClientManager().connect_to_client() as client:
    collection = client.collections.get("FD_Telemetry")

    # Test time-range query
    results = collection.query.fetch_objects(
        filters=...,
        limit=100
    )

    print(f"Retrieved {len(results.objects)} telemetry points")
```

### 4. Leverage Environment Context
Store intermediate results for subsequent tools:

```python
# In Tool A
tree_data.environment.set("fault_timestamp", alarm_time)

# In Tool B (later in execution)
fault_time = tree_data.environment.get("fault_timestamp")
```

### 5. Mock LLM Calls During Development
Use simple models for fast iteration:

```python
tree = Tree(
    base_model="gpt-4o-mini",  # Fast, cheap model
    complex_model="gpt-4o"     # Reserve for production
)
```

### 6. Create Realistic Demo Data
Script scenarios with known outcomes:

```bash
# Generate 7-day fault scenario
python scripts/create_fault_scenario.py \
    --asset FZ-123 \
    --fault fan_failure \
    --start 2024-03-15T14:30:00 \
    --duration 2h
```

---

## Next Steps

### Phase 1: MVP (2-3 weeks)
- [ ] Import telemetry data into Weaviate
- [ ] Import manual chunks from extraction pipeline
- [ ] Implement GetAssetHealth and GetAlarms tools
- [ ] Create basic health check workflow
- [ ] Test with simple queries

### Phase 2: Diagnostic Workflow (2-3 weeks)
- [ ] Implement GetTelemetryWindow tool
- [ ] Implement SearchDocuments tool
- [ ] Build cause analysis logic
- [ ] Create diagnostic checklist generator
- [ ] Test fault explanation scenarios

### Phase 3: Service Notes (1-2 weeks)
- [ ] Implement GenerateServiceNote tool
- [ ] Create FD_Cases collection
- [ ] Build case retrieval for similar incidents
- [ ] Add user feedback loop
- [ ] Test full diagnostic workflow

### Phase 4: Polish & Demo (1 week)
- [ ] Create demo script with 3-5 scenarios
- [ ] Build simple frontend (optional)
- [ ] Add visualizations for telemetry trends
- [ ] Documentation and user guide
- [ ] Record demo video

---

## Resources

- **Telemetry Data:** [docs/eda/README.md](eda/README.md)
- **Manual Extraction:** [features/extraction/README.md](../features/extraction/README.md)
- **Elysia Docs:** https://weaviate.github.io/elysia/
- **Weaviate API:** https://docs.weaviate.io/

---

**Status:** 📝 Implementation Guide (Not yet implemented)

**Last Updated:** 2024-11-10
