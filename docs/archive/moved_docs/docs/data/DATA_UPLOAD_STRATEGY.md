# VSM Data Upload Strategy

**Created**: November 11, 2024  
**Purpose**: Comprehensive strategy for uploading VSM data to Weaviate Cloud, optimized for Elysia agent usage  
**Status**: 📝 Strategy Document

---

## Executive Summary

This document outlines a **data upload strategy** that:
1. **Leverages Elysia's preprocessing system** for intelligent collection metadata
2. **Follows the hybrid storage approach** (Weaviate for discovery, local files for detail)
3. **Optimizes for agent retrieval patterns** based on SMIDO methodology
4. **Integrates diagram metadata** from parsed manuals
5. **Ensures cross-collection linking** for unified troubleshooting

**Key Principle**: Upload **metadata-rich, semantically searchable summaries** to Weaviate, while keeping **raw data** in local files for efficient on-demand queries.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Collection Schemas](#collection-schemas)
3. [Upload Sequence & Dependencies](#upload-sequence--dependencies)
4. [Elysia Preprocessing Integration](#elysia-preprocessing-integration)
5. [Data Enrichment Pipeline](#data-enrichment-pipeline)
6. [Cross-Collection Linking](#cross-collection-linking)
7. [Upload Scripts Structure](#upload-scripts-structure)
8. [Validation & Testing](#validation--testing)
9. [Implementation Checklist](#implementation-checklist)

---

## Architecture Overview

### Tool → Data Mapping

Each VSM agent tool requires specific data sources:

| Tool | Weaviate Collections | Local Files | Synthetic Data |
|------|---------------------|-------------|----------------|
| **ComputeWorldState** | - | Telemetry Parquet | WorldState Snapshots (reference) |
| **QueryTelemetryEvents** | VSM_TelemetryEvent | - | - |
| **SearchManualsBySMIDO** | VSM_ManualSections, VSM_Diagram | - | - |
| **QueryVlogCases** | VSM_VlogCase, VSM_VlogClip | Vlog .mov | - |
| **GetAlarms** | VSM_TelemetryEvent | - | - |
| **GetAssetHealth** | VSM_TelemetryEvent | Telemetry Parquet | Installation Context |
| **AnalyzeSensorPattern** | VSM_WorldStateSnapshot | Telemetry Parquet | WorldState Snapshots |

### Data Flow

```
RAW DATA → ENRICHMENT → WEAVIATE → PREPROCESSING → AGENT TOOLS
   ↓            ↓            ↓            ↓              ↓
Parquet    Event Det.   VSM_*      ELYSIA_     ComputeWorldState
JSONL      Section      Collections METADATA__  QueryTelemetry
.mov       Grouping                            SearchManuals
Mermaid    SMIDO Tag                           QueryVlogs
           Linking                             GetAlarms
                                              GetAssetHealth
                                              AnalyzeSensorPattern
```

### Storage Strategy

| Data Type | Weaviate | Local | Purpose | Agent Tool |
|-----------|----------|-------|---------|------------|
| **Telemetry Events** | VSM_TelemetryEvent | - | Historical incident search | QueryTelemetryEvents, GetAlarms |
| **Raw Telemetry** | - | Parquet | On-demand WorldState | ComputeWorldState, AnalyzeSensorPattern |
| **Manual Sections** | VSM_ManualSections | JSONL | SMIDO-filtered guidance | SearchManualsBySMIDO |
| **Diagrams** | VSM_Diagram | Mermaid | Logic flows for agent | SearchManualsBySMIDO (visual ref) |
| **Vlog Cases** | VSM_VlogCase | JSONL | Case matching | QueryVlogCases |
| **Vlog Clips** | VSM_VlogClip | JSONL | Detailed workflow | QueryVlogCases |
| **Videos** | - | .mov | Video playback | QueryVlogCases (reference) |
| **WorldState Snapshots** | VSM_WorldStateSnapshot | - | Pattern reference | AnalyzeSensorPattern |
| **Installation Context** | FD_Assets (enriched) | - | Asset metadata | GetAssetHealth |

**Rationale**: Hybrid storage optimized for tool performance:
- **Weaviate**: Semantic search (discovery) - aggregated metadata
- **Parquet**: Time-series computation - raw sensor data (785K rows)
- **Synthetic**: Pattern references and installation context

---

## Collection Schemas

### 1. VSM_TelemetryEvent

**Purpose**: Historical telemetry incidents with WorldState (W) features for semantic search and pattern matching.

**Key Concept**: Events capture when system went "uit balans" (out of balance), not just component failures.

**Schema** (based on `docs/data/telemetry_features.md`):

```python
properties = [
    # Identification
    Property(name="event_id", data_type=DataType.TEXT, filterable=True),
    Property(name="asset_id", data_type=DataType.TEXT, filterable=True),
    Property(name="t_start", data_type=DataType.DATE, filterable=True),
    Property(name="t_end", data_type=DataType.DATE, filterable=True),
    Property(name="duration_minutes", data_type=DataType.NUMBER, filterable=True),
    
    # Classification
    Property(name="failure_mode", data_type=DataType.TEXT, filterable=True),
    Property(name="failure_modes", data_type=DataType.TEXT_ARRAY, filterable=True),
    Property(name="affected_components", data_type=DataType.TEXT_ARRAY, filterable=True),
    Property(name="severity", data_type=DataType.TEXT, filterable=True),  # "critical", "warning", "info"
    
    # Aggregates (WorldState features)
    Property(name="room_temp_min", data_type=DataType.NUMBER),
    Property(name="room_temp_max", data_type=DataType.NUMBER),
    Property(name="room_temp_mean", data_type=DataType.NUMBER),
    Property(name="room_temp_trend", data_type=DataType.NUMBER),  # °C/hour
    Property(name="hot_gas_mean", data_type=DataType.NUMBER),
    Property(name="compressor_runtime_hours", data_type=DataType.NUMBER),
    Property(name="door_open_ratio", data_type=DataType.NUMBER),
    
    # Description (for vectorization)
    Property(name="description_nl", data_type=DataType.TEXT),  # Vectorized
    Property(name="worldstate_summary", data_type=DataType.TEXT),  # Vectorized
    
    # File reference (for detail lookup)
    Property(name="parquet_path", data_type=DataType.TEXT),
    Property(name="time_range_start", data_type=DataType.DATE),
    Property(name="time_range_end", data_type=DataType.DATE),
    
    # Cross-references
    Property(name="related_manual_sections", data_type=DataType.TEXT_ARRAY),  # section_ids
    Property(name="related_vlog_cases", data_type=DataType.TEXT_ARRAY),  # case_ids
    Property(name="related_diagrams", data_type=DataType.TEXT_ARRAY),  # diagram_ids
]
```

**Vectorization**: `description_nl` + `worldstate_summary` (combined)

**Size Estimate**: ~500-1000 events × ~2KB = **1-2 MB**

**Note**: Manual states "Een storing betekent dus niet altijd dat er een component defect is" - events represent system out of balance, not just broken parts.

---

### 2. VSM_ManualSections

**Purpose**: Logical sections from cooling manuals, tagged with SMIDO steps, failure modes, and components.

**Schema** (based on `docs/data/manuals_weaviate_design.md`):

```python
properties = [
    # Core identification
    Property(name="section_id", data_type=DataType.TEXT, filterable=True),
    Property(name="manual_id", data_type=DataType.TEXT, filterable=True),
    Property(name="manual_title", data_type=DataType.TEXT),
    Property(name="chunk_ids", data_type=DataType.TEXT_ARRAY),
    
    # Content
    Property(name="title", data_type=DataType.TEXT),  # Vectorized
    Property(name="body_text", data_type=DataType.TEXT),  # Vectorized
    Property(name="language", data_type=DataType.TEXT, filterable=True),
    Property(name="page_start", data_type=DataType.INT, filterable=True),
    Property(name="page_end", data_type=DataType.INT, filterable=True),
    Property(name="page_range", data_type=DataType.TEXT),
    
    # Classification
    Property(name="smido_step", data_type=DataType.TEXT, filterable=True),
    Property(name="smido_steps", data_type=DataType.TEXT_ARRAY, filterable=True),
    Property(name="content_type", data_type=DataType.TEXT, filterable=True),  # "uitleg", "flowchart", "tabel", "opgave"
    Property(name="failure_mode", data_type=DataType.TEXT, filterable=True),
    Property(name="failure_modes", data_type=DataType.TEXT_ARRAY, filterable=True),
    Property(name="component", data_type=DataType.TEXT, filterable=True),
    Property(name="components", data_type=DataType.TEXT_ARRAY, filterable=True),
    
    # Metadata
    Property(name="contains_images", data_type=DataType.BOOL, filterable=True),
    Property(name="image_descriptions", data_type=DataType.TEXT_ARRAY),
    Property(name="contains_table", data_type=DataType.BOOL, filterable=True),
    Property(name="is_case_study", data_type=DataType.BOOL, filterable=True),
    Property(name="case_title", data_type=DataType.TEXT),
    Property(name="difficulty_level", data_type=DataType.TEXT, filterable=True),
    
    # Diagram integration
    Property(name="related_diagram_ids", data_type=DataType.TEXT_ARRAY),  # Links to VSM_Diagram
]
```

**Vectorization**: `title` + `body_text` (combined)

**Size Estimate**: ~170-240 sections × ~3KB = **500-700 KB**

---

### 3. VSM_VlogCase

**Purpose**: Aggregated video cases (A1-A5) with complete problem-triage-solution workflows.

**Schema** (based on `docs/data/vlogs_structure.md`):

```python
properties = [
    # Identification
    Property(name="case_id", data_type=DataType.TEXT, filterable=True),  # "A1", "A2", etc.
    Property(name="case_title", data_type=DataType.TEXT),  # Vectorized
    Property(name="clip_ids", data_type=DataType.TEXT_ARRAY),  # ["A1_1", "A1_2", "A1_3"]
    
    # Content
    Property(name="problem_summary", data_type=DataType.TEXT),  # Vectorized
    Property(name="root_cause", data_type=DataType.TEXT),  # Vectorized
    Property(name="solution_summary", data_type=DataType.TEXT),  # Vectorized
    Property(name="transcript_nl", data_type=DataType.TEXT),  # Vectorized
    
    # Classification
    Property(name="failure_mode", data_type=DataType.TEXT, filterable=True),
    Property(name="failure_modes", data_type=DataType.TEXT_ARRAY, filterable=True),
    Property(name="component_primary", data_type=DataType.TEXT, filterable=True),
    Property(name="components", data_type=DataType.TEXT_ARRAY, filterable=True),
    Property(name="smido_steps", data_type=DataType.TEXT_ARRAY, filterable=True),
    Property(name="smido_step_primary", data_type=DataType.TEXT, filterable=True),
    
    # Sensor correlation
    Property(name="world_state_pattern", data_type=DataType.TEXT),  # Vectorized
    Property(name="typical_sensor_conditions", data_type=DataType.TEXT),  # JSON string
    
    # Cross-references
    Property(name="related_manual_sections", data_type=DataType.TEXT_ARRAY),  # section_ids
    Property(name="related_telemetry_events", data_type=DataType.TEXT_ARRAY),  # event_ids
    Property(name="related_diagrams", data_type=DataType.TEXT_ARRAY),  # diagram_ids
]
```

**Vectorization**: `case_title` + `problem_summary` + `root_cause` + `solution_summary` + `transcript_nl` + `world_state_pattern` (combined)

**Size Estimate**: 5 cases × ~5KB = **25 KB**

---

### 4. VSM_VlogClip

**Purpose**: Individual video clips with timestamps and step-by-step breakdowns.

**Schema**:

```python
properties = [
    # Identification
    Property(name="clip_id", data_type=DataType.TEXT, filterable=True),  # "A1_1", "A1_2", etc.
    Property(name="case_id", data_type=DataType.TEXT, filterable=True),  # "A1"
    Property(name="clip_number", data_type=DataType.INT, filterable=True),  # 1, 2, or 3
    Property(name="video_filename", data_type=DataType.TEXT),
    Property(name="video_path", data_type=DataType.TEXT),  # Local path
    Property(name="duration_seconds", data_type=DataType.NUMBER, filterable=True),
    
    # Content
    Property(name="title", data_type=DataType.TEXT),  # Vectorized
    Property(name="problem_summary", data_type=DataType.TEXT),  # Vectorized
    Property(name="root_cause", data_type=DataType.TEXT),  # Vectorized
    Property(name="solution_summary", data_type=DataType.TEXT),  # Vectorized
    Property(name="steps_text", data_type=DataType.TEXT),  # Combined step descriptions, vectorized
    
    # Classification
    Property(name="failure_mode", data_type=DataType.TEXT, filterable=True),
    Property(name="failure_modes", data_type=DataType.TEXT_ARRAY, filterable=True),
    Property(name="component_primary", data_type=DataType.TEXT, filterable=True),
    Property(name="components", data_type=DataType.TEXT_ARRAY, filterable=True),
    Property(name="smido_step_primary", data_type=DataType.TEXT, filterable=True),
    Property(name="smido_steps", data_type=DataType.TEXT_ARRAY, filterable=True),
    
    # Metadata
    Property(name="tags", data_type=DataType.TEXT_ARRAY, filterable=True),
    Property(name="skill_level", data_type=DataType.TEXT, filterable=True),
    Property(name="is_complete_case", data_type=DataType.BOOL, filterable=True),
]
```

**Vectorization**: `title` + `problem_summary` + `root_cause` + `solution_summary` + `steps_text` (combined)

**Size Estimate**: 15 clips × ~3KB = **45 KB**

---

### 5. VSM_Diagram

**Purpose**: Visual logic diagrams for SearchManualsBySMIDO tool - returned alongside text sections for visual explanation.

**Schema**:

```python
properties = [
    Property(name="diagram_id", data_type=DataType.TEXT, filterable=True),
    Property(name="title", data_type=DataType.TEXT),  # Vectorized
    Property(name="description", data_type=DataType.TEXT),  # Vectorized
    Property(name="agent_usage", data_type=DataType.TEXT),  # When to show
    Property(name="mermaid_code", data_type=DataType.TEXT),
    Property(name="source_chunk_id", data_type=DataType.TEXT, filterable=True),
    Property(name="smido_phases", data_type=DataType.TEXT_ARRAY, filterable=True),
    Property(name="failure_modes", data_type=DataType.TEXT_ARRAY, filterable=True),
    Property(name="diagram_type", data_type=DataType.TEXT, filterable=True),
]
```

**Agent Usage**: SearchManualsBySMIDO returns diagrams when:
- Query matches SMIDO phase + diagram explains concept
- Failure mode matches diagram topic
- User asks "how" questions (diagrams show process)

**Size**: 9 diagrams × ~2KB = **18 KB**

---

## Upload Sequence & Dependencies

**Principle**: Upload in order of agent tool dependencies.

### Phase 1: Core Collections (Agent Discovery)

1. **VSM_ManualSections** + **VSM_Diagram** (parallel)
   - SearchManualsBySMIDO needs both for SMIDO-filtered queries
   - Diagrams link to sections via source_chunk_id
   
2. **VSM_TelemetryEvent**
   - QueryTelemetryEvents + GetAlarms need historical incidents
   - Link to manual sections (failure mode matching)

3. **VSM_VlogClip** + **VSM_VlogCase** (parallel)
   - QueryVlogCases needs both for case matching
   - Link to manual sections and telemetry events

### Phase 2: Synthetic Data (Agent References)

4. **VSM_WorldStateSnapshot**
   - AnalyzeSensorPattern needs reference patterns
   - Generated from real events + manual descriptions

5. **Enrich FD_Assets**
   - GetAssetHealth needs installation context
   - Add component metadata, operational history

### Phase 3: Integration

6. **Cross-Collection Linking**
   - Semantic + deterministic linking
   - Verify tool query paths work

7. **Elysia Preprocessing**
   - Generate ELYSIA_METADATA__ for all collections
   - Test tool queries against metadata

---

## Elysia Preprocessing Integration

### Why Preprocessing Matters

Elysia's `preprocess()` function:
1. **Analyzes schema** and generates property descriptions
2. **Creates LLM summaries** of collection purpose and content
3. **Maps properties** to frontend display types (table, document, etc.)
4. **Generates example queries** for the agent
5. **Stores metadata** in `ELYSIA_METADATA__` collection

**Without preprocessing**, Elysia's Query tool cannot intelligently query your collections.

### Preprocessing Configuration

For each VSM collection, we should:

1. **Set appropriate display types**:
   - `VSM_ManualSections` → `"document"` (text-heavy, narrative)
   - `VSM_TelemetryEvent` → `"table"` (structured data)
   - `VSM_VlogCase` → `"conversation"` or `"document"` (workflow)
   - `VSM_VlogClip` → `"message"` (individual steps)
   - `VSM_Diagram` → `"document"` (visual reference)

2. **Provide sample data**:
   - Ensure collections have at least 10 objects before preprocessing
   - Include diverse examples (different SMIDO steps, failure modes)

3. **Run preprocessing**:
   ```python
   from elysia import preprocess
   
   preprocess([
       "VSM_TelemetryEvent",
       "VSM_ManualSections",
       "VSM_VlogCase",
       "VSM_VlogClip",
       "VSM_Diagram"
   ])
   ```

### Expected Preprocessing Output

After preprocessing, `ELYSIA_METADATA__` will contain entries like:

```json
{
  "name": "VSM_ManualSections",
  "summary": "Sections from cooling technology manuals organized by SMIDO methodology steps...",
  "fields": [
    {
      "name": "title",
      "description": "Section title or heading from the manual",
      "type": "text"
    },
    {
      "name": "smido_step",
      "description": "SMIDO methodology step this section relates to (melding, technisch, diagnose, etc.)",
      "type": "text",
      "groups": {"melding": 15, "technisch": 12, "3P_power": 8, ...}
    }
  ],
  "mappings": {
    "document": {
      "title": "title",
      "content": "body_text",
      "metadata": ["smido_step", "failure_modes", "page_range"]
    }
  }
}
```

This metadata enables Elysia's Query tool to:
- Understand what each collection contains
- Generate appropriate filters (e.g., `smido_step == "melding"`)
- Format results for display
- Suggest relevant collections for queries

---

## Data Enrichment Pipeline

### 1. Telemetry Event Detection

**Script**: `features/telemetry_vsm/src/detect_events.py`

**Process**:
1. Load parquet file
2. Detect incident periods:
   - Continuous periods where flags = True
   - OR room_temp > -18°C for >30 minutes
3. For each event:
   - Compute WorldState features (min/max/mean, trends)
   - Generate natural language description
   - Classify failure mode (rule-based or LLM)
   - Identify affected components
4. Output: JSONL with event objects

**Example Event**:
```json
{
  "event_id": "evt_2024_10_15_1430",
  "asset_id": "135_1570",
  "t_start": "2024-10-15T14:30:00Z",
  "t_end": "2024-10-15T16:45:00Z",
  "duration_minutes": 135,
  "failure_mode": "ingevroren_verdamper",
  "failure_modes": ["ingevroren_verdamper", "te_hoge_temperatuur"],
  "affected_components": ["verdamper", "ontdooiheater", "thermostat"],
  "severity": "critical",
  "room_temp_min": -12.5,
  "room_temp_max": -8.2,
  "room_temp_mean": -10.1,
  "room_temp_trend": 2.8,
  "description_nl": "Koelcel bereikt temperatuur niet. Verdamper volledig bevroren. Temperatuur stijgt gestaag van -12.5°C naar -8.2°C over 2.25 uur.",
  "worldstate_summary": "Room temp rising (2.8°C/hour), evaporator frozen, defrost cycle not working, hot gas temp low",
  "parquet_path": "features/telemetry/timeseries_freezerdata/135_1570_cleaned_with_flags.parquet",
  "time_range_start": "2024-10-15T14:30:00Z",
  "time_range_end": "2024-10-15T16:45:00Z"
}
```

---

### 2. Manual Section Grouping

**Script**: `features/manuals_vsm/src/parse_sections.py`

**Process**:
1. Load text chunks from JSONL
2. Group chunks by heading hierarchy:
   - Detect heading patterns (H1, H2, H3)
   - Combine 2-4 chunks per logical section
3. Classify sections:
   - `smido_step`: Keyword matching + LLM classification
   - `content_type`: Detect tables, flowcharts, case studies
   - `failure_modes`: Extract from body text (LLM)
   - `components`: Named entity recognition
4. Link to diagrams:
   - Match `source_chunk_id` from diagrams to chunk_ids in section
5. Output: JSONL with section objects

**Example Section**:
```json
{
  "section_id": "storingzoeken_smido_melding_001",
  "manual_id": "storingzoeken-koeltechniek_theorie_179",
  "title": "Melding",
  "body_text": "Is de melding compleet, waar staat de installatie...",
  "smido_step": "melding",
  "content_type": "uitleg",
  "page_range": "8",
  "related_diagram_ids": ["smido_main_flowchart"]
}
```

---

### 3. Vlog Enrichment

**Script**: `features/vlogs_vsm/src/enrich_vlog_metadata.py`

**Process**:
1. Load existing `vlogs_vsm_annotations.jsonl` (20 records)
2. For each clip:
   - Extract `vlog_id`, `vlog_set` from filename
   - Classify SMIDO steps (LLM-based)
   - Standardize failure modes to controlled vocabulary
   - Generate `world_state_pattern` from problem/root cause
   - Link to related manual sections (semantic matching)
3. Aggregate clips into cases (A1-A5)
4. Output: Enriched JSONL for clips + cases

---

### 4. Diagram Metadata Extraction

**Script**: `features/diagrams_vsm/src/extract_diagram_metadata.py`

**Process**:
1. Parse all `.mermaid` files from `docs/diagrams/`
2. Extract metadata headers (title, source, chunk, SMIDO phases, etc.)
3. Parse Mermaid code to extract:
   - Components mentioned
   - Failure modes referenced
   - SMIDO phases covered
4. Output: JSONL with diagram objects

---

## Cross-Collection Linking

### Linking Strategy

After all collections are uploaded, we need to create cross-references:

1. **TelemetryEvent ↔ ManualSections**:
   - Match by failure mode
   - Match by component
   - Semantic similarity on descriptions

2. **TelemetryEvent ↔ VlogCase**:
   - Match by failure mode
   - Match by world_state_pattern similarity

3. **VlogCase ↔ ManualSections**:
   - Match by SMIDO step
   - Match by failure mode
   - Semantic similarity on problem/solution

4. **All ↔ Diagrams**:
   - ManualSections → Diagrams (via chunk_id)
   - TelemetryEvent → Diagrams (via failure mode/components)
   - VlogCase → Diagrams (via SMIDO step)

### Linking Script

**Script**: `features/integration_vsm/src/link_entities_weaviate.py`

**Process**:
1. Query all collections
2. For each entity, find related entities:
   - Use semantic search (hybrid query)
   - Use filter matching (failure_mode, components, SMIDO steps)
   - Use deterministic rules (chunk_id matching)
3. Update entities with `related_*` properties
4. Verify bidirectional links where appropriate

---

## Upload Scripts Structure

### Directory Structure

```
features/
├── telemetry_vsm/
│   └── src/
│       ├── detect_events.py          # Event detection from parquet
│       └── import_telemetry_weaviate.py  # Upload events to Weaviate
│
├── manuals_vsm/
│   └── src/
│       ├── parse_sections.py         # Group chunks into sections
│       ├── classify_smido.py         # SMIDO classification
│       └── import_manuals_weaviate.py  # Upload sections to Weaviate
│
├── vlogs_vsm/
│   └── src/
│       ├── enrich_vlog_metadata.py   # Enrich existing JSONL
│       └── import_vlogs_weaviate.py   # Upload clips + cases to Weaviate
│
├── diagrams_vsm/
│   └── src/
│       ├── extract_diagram_metadata.py  # Parse Mermaid files
│       └── import_diagrams_weaviate.py  # Upload diagrams to Weaviate
│
└── integration_vsm/
    └── src/
        └── link_entities_weaviate.py  # Cross-collection linking
```

### Common Upload Pattern

Each import script follows this pattern:

```python
import weaviate
from weaviate.classes.config import Configure, Property, DataType
from dotenv import load_dotenv
import json

load_dotenv()

# 1. Connect to Weaviate Cloud
client = weaviate.connect_to_weaviate_cloud(
    cluster_url=os.environ["WEAVIATE_URL"],
    auth_credentials=Auth.api_key(os.environ["WEAVIATE_API_KEY"])
)

# 2. Create collection schema
collection = client.collections.create(
    name="VSM_CollectionName",
    vectorizer_config=Configure.Vectorizer.text2vec_weaviate(...),
    properties=[...]
)

# 3. Load enriched data (JSONL)
with open("path/to/enriched_data.jsonl", "r") as f:
    data = [json.loads(line) for line in f]

# 4. Batch import
with collection.batch.fixed_size(batch_size=200) as batch:
    for item in data:
        batch.add_object(item)

# 5. Verify
print(f"Imported {collection.aggregate.over_all(total_count=True).total_count} objects")
```

---

## Validation & Testing

### Pre-Upload Validation

1. **Schema Validation**:
   - Verify all required properties exist
   - Check data types match schema
   - Validate controlled vocabularies (SMIDO steps, failure modes)

2. **Data Quality Checks**:
   - No null values in required fields
   - Valid date formats
   - Valid UUIDs for references
   - Text fields not empty

3. **Size Estimates**:
   - Verify collection sizes match expectations
   - Check vector dimensions are reasonable

### Post-Upload Validation

1. **Collection Verification**:
   ```python
   # Check object counts
   assert collection.aggregate.over_all(total_count=True).total_count == expected_count
   
   # Sample queries
   results = collection.query.fetch_objects(limit=5)
   assert len(results.objects) == 5
   ```

2. **Query Testing**:
   - Test SMIDO-step filtered queries
   - Test failure mode matching
   - Test semantic search
   - Test cross-collection links

3. **Elysia Preprocessing Verification**:
   ```python
   # Check metadata was created
   metadata_collection = client.collections.get("ELYSIA_METADATA__")
   metadata = metadata_collection.query.fetch_objects(
       where={"path": ["name"], "operator": "Equal", "valueText": "VSM_ManualSections"}
   )
   assert len(metadata.objects) == 1
   ```

---

## Implementation Checklist

### Phase 1: Foundation ✅

- [ ] Create `features/diagrams_vsm/src/extract_diagram_metadata.py`
- [ ] Create `features/diagrams_vsm/src/import_diagrams_weaviate.py`
- [ ] Upload VSM_Diagram collection
- [ ] Create `features/manuals_vsm/src/parse_sections.py`
- [ ] Create `features/manuals_vsm/src/classify_smido.py`
- [ ] Create `features/manuals_vsm/src/import_manuals_weaviate.py`
- [ ] Upload VSM_ManualSections collection

### Phase 2: Events & Cases ✅

- [ ] Create `features/telemetry_vsm/src/detect_events.py`
- [ ] Create `features/telemetry_vsm/src/import_telemetry_weaviate.py`
- [ ] Upload VSM_TelemetryEvent collection
- [ ] Create `features/vlogs_vsm/src/enrich_vlog_metadata.py`
- [ ] Create `features/vlogs_vsm/src/import_vlogs_weaviate.py`
- [ ] Upload VSM_VlogClip collection
- [ ] Upload VSM_VlogCase collection

### Phase 3: Integration ✅

- [ ] Create `features/integration_vsm/src/link_entities_weaviate.py`
- [ ] Run cross-collection linking
- [ ] Verify all links are bidirectional where appropriate

### Phase 4: Elysia Integration ✅

- [ ] Run `preprocess()` on all VSM_* collections
- [ ] Verify `ELYSIA_METADATA__` entries
- [ ] Test Query tool with sample queries
- [ ] Verify display types are correct

### Phase 5: Documentation ✅

- [ ] Document upload process
- [ ] Create troubleshooting guide
- [ ] Update `todo.md` with completion status

---

## Key Considerations

### 1. Vectorization Strategy

- **Use `text2vec-weaviate`** (built-in, no API key) for MVP
- **Consider `text2vec-openai`** for better quality (requires API key)
- **Combine multiple text fields** for richer semantic representation

### 2. Filterable Properties

- Make frequently filtered properties filterable:
  - `smido_step`, `failure_mode`, `component` (for structured queries)
  - `severity`, `content_type` (for filtering)
  - Dates, numbers (for range queries)

### 3. Batch Import Performance

- Use `batch.fixed_size(batch_size=200)` for optimal performance
- Monitor import progress (print every 100 objects)
- Handle errors gracefully (check `batch.number_errors`)

### 4. Data Freshness

- Keep local files as source of truth
- Re-run enrichment scripts if source data changes
- Version control enriched JSONL files

### 5. Cost Optimization

- Weaviate Cloud charges by:
  - Storage (vectors + metadata)
  - Query operations
- Our collections are small (~2-3 MB total)
- Estimated cost: <$10/month for demo usage

---

## Next Steps

1. **Start with VSM_Diagram** (simplest, no dependencies)
2. **Then VSM_ManualSections** (foundation for other collections)
3. **Then events and vlogs** (can link to manuals)
4. **Finally cross-linking** (requires all collections)

**Priority**: Focus on **A3 "Frozen Evaporator"** scenario first - ensure all related data is uploaded and linked correctly.

---

## Synthetic Data & Context

**Note**: See [SYNTHETIC_DATA_STRATEGY.md](SYNTHETIC_DATA_STRATEGY.md) for complete details on synthetic data requirements.

### FD_* Collections (MVP/Test Data)

The codebase includes **FD_* collections** (`FD_Assets`, `FD_Alarms`, `FD_Cases`) that are **intentionally separate** from VSM_* collections:

- **Purpose**: MVP/demo testing, Elysia framework validation
- **Status**: ✅ Already seeded via `scripts/seed_assets_alarms.py`
- **Action**: No changes needed - these serve as test collections

### Synthetic WorldState Snapshots

**Gap Identified**: `todo.md` mentions "Synthetic WorldState/Context (C, W)" but this is not addressed in the current strategy.

**Required**: `VSM_WorldStateSnapshot` collection for:
- Pre-computed WorldState patterns for common failure modes
- Fast pattern matching in agent queries
- Demo scenario support

**Priority**: Medium (can be added after core collections)

**See**: `SYNTHETIC_DATA_STRATEGY.md` for implementation details.

---

**Status**: 📝 Strategy Complete - Ready for Implementation  
**Last Updated**: November 11, 2024  
**Related**: See [SYNTHETIC_DATA_STRATEGY.md](SYNTHETIC_DATA_STRATEGY.md) for synthetic data requirements

