# Vlogs Structure Proposal

## Overview

This document proposes the target JSON structure for vlog metadata after Gemini 2.5 Pro processing, and the corresponding Weaviate schema for the `ServiceVlogs` collection.

---

## Current Gemini Output Structure

Based on the processed example (A1_1.mov), Gemini 2.5 Pro produces:

```json
{
  "video_filename": "A1_1.mov",
  "video_local_path": "/path/to/A1_1.mov",
  "gemini_file_uri": "https://generativelanguage.googleapis.com/v1beta/files/...",
  "rag_blob_ref": "/path/to/A1_1.mov",
  "payload": {
    "language": "nl",
    "installation_type": "Koelinstallatie (trainingsopstelling)",
    "environment_context": "Trainingscentrum / werkplaats",
    "problem_summary": "Bij aankomst op locatie is de temperatuur...",
    "root_cause": "De condensorventilatoren draaien niet...",
    "solution_summary": null,
    "steps": [
      {
        "kind": "problem",
        "title": "Vaststelling te hoge temperatuur",
        "description": "Bij aankomst wordt geconstateerd...",
        "start_time_s": 1.0,
        "end_time_s": 9.0
      },
      {
        "kind": "triage",
        "title": "Visuele inspectie condensorunit",
        "description": "Tijdens een visuele inspectie...",
        "start_time_s": 9.0,
        "end_time_s": 15.0
      }
    ],
    "tags": ["condensorventilator", "warmteafvoer", ...]
  }
}
```

---

## Proposed Enhanced Structure

### Complete Vlog Record (for Weaviate ingestion)

```json
{
  "vlog_id": "A1_1",
  "vlog_set": "A1",
  "clip_number": 1,
  "video_filename": "A1_1.mov",
  "video_path": "features/vlogs_vsm/A1_1.mov",
  "video_blob_ref": "gs://vsm-demo/vlogs/A1_1.mov",
  "gemini_file_uri": "https://generativelanguage.googleapis.com/v1beta/files/...",

  "title": "Condensorventilator storing - Probleem identificatie",
  "language": "nl",
  "duration_seconds": 19.0,

  "installation_type": "training_setup",
  "environment_context": "Trainingscentrum / werkplaats",

  "problem_summary": "Bij aankomst op locatie is de temperatuur in de koelcel te hoog...",
  "root_cause": "De condensorventilatoren draaien niet...",
  "solution_summary": "Condensorventilatoren hersteld/vervangen (te verifiëren in vervolg-clip)",

  "steps": [
    {
      "kind": "problem",
      "title": "Vaststelling te hoge temperatuur",
      "description": "Bij aankomst wordt geconstateerd...",
      "start_time_s": 1.0,
      "end_time_s": 9.0
    },
    {
      "kind": "triage",
      "title": "Visuele inspectie condensorunit",
      "description": "Tijdens een visuele inspectie...",
      "start_time_s": 9.0,
      "end_time_s": 15.0
    },
    {
      "kind": "triage",
      "title": "Fysieke controle warmteophoping",
      "description": "Door de condensor fysiek te controleren...",
      "start_time_s": 15.0,
      "end_time_s": 19.0
    }
  ],

  "failure_mode": "ventilator_defect",
  "failure_modes": ["ventilator_defect", "te_hoge_temperatuur"],

  "components": ["condensor", "ventilator"],
  "component_primary": "ventilator",

  "smido_steps": ["melding", "technisch", "installatie_vertrouwd"],
  "smido_step_primary": "technisch",

  "world_state_pattern": "Room temp high, condenser hot, fans not running",
  "typical_sensor_conditions": {
    "sGekoeldeRuimte": "> -18°C (too warm)",
    "sHeetgasLeiding": "> 60°C (high)",
    "sOmgeving": "normal"
  },

  "tags": ["condensorventilator", "warmteafvoer", "storing diagnose", "hoge condensatiedruk"],

  "skill_level": "beginner",
  "estimated_difficulty": "easy",

  "related_clips": ["A1_2", "A1_3"],
  "is_complete_case": false,
  "case_continuation": "A1_2",

  "transcript_nl": "Optioneel: Volledige Nederlandse transcript...",
  "transcript_en": "Optioneel: Engelse vertaling...",

  "metadata": {
    "processed_date": "2024-11-10",
    "gemini_model": "gemini-2.5-pro",
    "processing_version": "1.0"
  }
}
```

---

## Field Definitions

### Core Identification

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `vlog_id` | TEXT | Yes | Unique identifier (e.g., "A1_1") |
| `vlog_set` | TEXT | Yes | Case/scenario grouping (e.g., "A1") |
| `clip_number` | INT | Yes | Sequence within case (1, 2, or 3) |
| `video_filename` | TEXT | Yes | Original filename |
| `video_path` | TEXT | Yes | Local file path |
| `video_blob_ref` | TEXT | No | Cloud storage reference (GCS/S3) |
| `gemini_file_uri` | TEXT | No | Gemini Files API URI |

### Content Metadata

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | TEXT | Yes | Human-readable title |
| `language` | TEXT | Yes | Primary language code ("nl", "en") |
| `duration_seconds` | FLOAT | Yes | Video duration |
| `installation_type` | TEXT | Yes | Type of installation shown |
| `environment_context` | TEXT | No | Where installation is located |

### Problem-Solution Content

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `problem_summary` | TEXT | Yes | 1-3 sentence problem description |
| `root_cause` | TEXT | Yes | Identified root cause |
| `solution_summary` | TEXT | No | Solution description (may be in later clip) |
| `steps` | ARRAY[Step] | Yes | Ordered workflow steps with timestamps |

### Step Object Structure

```json
{
  "kind": "problem" | "triage" | "solution",
  "title": "Short step name",
  "description": "Detailed explanation",
  "start_time_s": 1.0,
  "end_time_s": 9.0
}
```

### Classification

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `failure_mode` | TEXT | Yes | Primary failure mode |
| `failure_modes` | TEXT[] | Yes | All applicable failure modes |
| `components` | TEXT[] | Yes | Components involved |
| `component_primary` | TEXT | Yes | Main component of focus |
| `smido_steps` | TEXT[] | Yes | SMIDO steps demonstrated |
| `smido_step_primary` | TEXT | Yes | Primary SMIDO step |

### Sensor Correlation

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `world_state_pattern` | TEXT | No | Natural language description of sensor state |
| `typical_sensor_conditions` | OBJECT | No | Expected telemetry patterns |

**Example**:
```json
{
  "sGekoeldeRuimte": "> -18°C",
  "sHeetgasLeiding": "> 60°C",
  "sDeurcontact": "normal"
}
```

### Tags and Difficulty

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tags` | TEXT[] | Yes | Short keywords for retrieval |
| `skill_level` | TEXT | No | "beginner", "intermediate", "advanced" |
| `estimated_difficulty` | TEXT | No | "easy", "medium", "hard" |

### Relationships

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `related_clips` | TEXT[] | No | IDs of related clips (e.g., rest of case) |
| `is_complete_case` | BOOLEAN | Yes | Does this clip contain full workflow? |
| `case_continuation` | TEXT | No | Next clip ID if case continues |

### Optional Rich Content

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `transcript_nl` | TEXT | No | Full Dutch transcript |
| `transcript_en` | TEXT | No | English translation |
| `key_frames` | ARRAY | No | URLs to extracted key frame images |
| `thumbnail_url` | TEXT | No | Preview thumbnail |

### Processing Metadata

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `metadata` | OBJECT | Yes | Processing info (date, model, version) |

---

## Weaviate Collection Schema: `ServiceVlogs`

### Purpose

Store vlog metadata for RAG retrieval based on:
1. **Failure mode matching** - Find vlogs showing similar problems
2. **WorldState matching** - Find vlogs with similar sensor patterns
3. **SMIDO step guidance** - Show relevant examples for current step
4. **Component-specific examples** - Find vlogs about specific components

---

## Properties Schema

### Core Identification

| Property | Type | Filterable | Vectorized | Description |
|----------|------|------------|------------|-------------|
| `vlog_id` | TEXT | Yes | No | Unique ID (e.g., "A1_1") |
| `vlog_set` | TEXT | Yes | No | Case grouping (e.g., "A1") |
| `clip_number` | INT | Yes | No | Sequence number (1-3) |
| `video_filename` | TEXT | Yes | No | Original filename |
| `video_blob_ref` | TEXT | No | No | Cloud storage reference |

### Content

| Property | Type | Filterable | Vectorized | Description |
|----------|------|------------|------------|-------------|
| `title` | TEXT | No | **Yes** | Vlog title |
| `language` | TEXT | Yes | No | Language code |
| `duration_seconds` | FLOAT | Yes | No | Duration |
| `problem_summary` | TEXT | No | **Yes** | Problem description |
| `root_cause` | TEXT | No | **Yes** | Root cause |
| `solution_summary` | TEXT | No | **Yes** | Solution description |
| `steps_text` | TEXT | No | **Yes** | Combined text of all step descriptions |

### Classification

| Property | Type | Filterable | Vectorized | Description |
|----------|------|------------|------------|-------------|
| `failure_mode` | TEXT | Yes | No | Primary failure mode |
| `failure_modes` | TEXT[] | Yes | No | All failure modes |
| `component_primary` | TEXT | Yes | No | Main component |
| `components` | TEXT[] | Yes | No | All components |
| `smido_step_primary` | TEXT | Yes | No | Primary SMIDO step |
| `smido_steps` | TEXT[] | Yes | No | All SMIDO steps |

### Sensor Correlation

| Property | Type | Filterable | Vectorized | Description |
|----------|------|------------|------------|-------------|
| `world_state_pattern` | TEXT | No | **Yes** | Sensor state description |
| `typical_sensor_conditions` | TEXT | No | **Yes** | JSON string of sensor patterns |

### Tags and Metadata

| Property | Type | Filterable | Vectorized | Description |
|----------|------|------------|------------|-------------|
| `tags` | TEXT[] | Yes | No | Keyword tags |
| `skill_level` | TEXT | Yes | No | Difficulty level |
| `is_complete_case` | BOOLEAN | Yes | No | Full workflow? |

---

## Vectorization Strategy

### Content Vector

Vectorize the following combined text:
- `title`
- `problem_summary`
- `root_cause`
- `solution_summary`
- `steps_text`
- `world_state_pattern`

This creates a rich semantic representation for similarity search.

---

## Sample Weaviate Object

```json
{
  "vlog_id": "A1_1",
  "vlog_set": "A1",
  "clip_number": 1,
  "video_filename": "A1_1.mov",
  "video_blob_ref": "gs://vsm-demo/vlogs/A1_1.mov",

  "title": "Condensorventilator storing - Probleem identificatie",
  "language": "nl",
  "duration_seconds": 19.0,

  "problem_summary": "Bij aankomst op locatie is de temperatuur in de koelcel te hoog. De installatie is wel actief, maar er is sprake van onvoldoende warmteafvoer.",
  "root_cause": "De condensorventilatoren draaien niet. Hierdoor kan de condensor zijn warmte niet kwijt.",
  "solution_summary": null,
  "steps_text": "Vaststelling te hoge temperatuur: Bij aankomst wordt geconstateerd... Visuele inspectie condensorunit: Tijdens inspectie...",

  "failure_mode": "ventilator_defect",
  "failure_modes": ["ventilator_defect", "te_hoge_temperatuur"],
  "component_primary": "ventilator",
  "components": ["condensor", "ventilator"],
  "smido_step_primary": "technisch",
  "smido_steps": ["melding", "technisch", "installatie_vertrouwd"],

  "world_state_pattern": "Room temperature rising, condenser hot to touch, fans not spinning, system running",
  "typical_sensor_conditions": "{\"sGekoeldeRuimte\": \"> -18°C\", \"sHeetgasLeiding\": \"> 60°C\"}",

  "tags": ["condensorventilator", "warmteafvoer", "hoge condensatiedruk"],
  "skill_level": "beginner",
  "is_complete_case": false
}
```

---

## Python Schema Definition

```python
import weaviate
from weaviate.classes.config import Configure, Property, DataType

def create_service_vlogs_collection(client):
    """Create the ServiceVlogs collection"""

    client.collections.create(
        name="ServiceVlogs",
        description="Service engineer video logs showing troubleshooting workflows",
        vectorizer_config=Configure.Vectorizer.text2vec_openai(
            model="text-embedding-3-small",
            vectorize_collection_name=False
        ),
        properties=[
            # Core identification
            Property(name="vlog_id", data_type=DataType.TEXT,
                     skip_vectorization=True, filterable=True),
            Property(name="vlog_set", data_type=DataType.TEXT,
                     skip_vectorization=True, filterable=True),
            Property(name="clip_number", data_type=DataType.INT,
                     skip_vectorization=True, filterable=True),
            Property(name="video_filename", data_type=DataType.TEXT,
                     skip_vectorization=True),
            Property(name="video_blob_ref", data_type=DataType.TEXT,
                     skip_vectorization=True),

            # Content (vectorized)
            Property(name="title", data_type=DataType.TEXT),
            Property(name="language", data_type=DataType.TEXT,
                     skip_vectorization=True, filterable=True),
            Property(name="duration_seconds", data_type=DataType.NUMBER,
                     skip_vectorization=True, filterable=True),
            Property(name="problem_summary", data_type=DataType.TEXT),
            Property(name="root_cause", data_type=DataType.TEXT),
            Property(name="solution_summary", data_type=DataType.TEXT),
            Property(name="steps_text", data_type=DataType.TEXT),

            # Classification
            Property(name="failure_mode", data_type=DataType.TEXT,
                     skip_vectorization=True, filterable=True),
            Property(name="failure_modes", data_type=DataType.TEXT_ARRAY,
                     skip_vectorization=True, filterable=True),
            Property(name="component_primary", data_type=DataType.TEXT,
                     skip_vectorization=True, filterable=True),
            Property(name="components", data_type=DataType.TEXT_ARRAY,
                     skip_vectorization=True, filterable=True),
            Property(name="smido_step_primary", data_type=DataType.TEXT,
                     skip_vectorization=True, filterable=True),
            Property(name="smido_steps", data_type=DataType.TEXT_ARRAY,
                     skip_vectorization=True, filterable=True),

            # Sensor correlation
            Property(name="world_state_pattern", data_type=DataType.TEXT),
            Property(name="typical_sensor_conditions", data_type=DataType.TEXT),

            # Tags and metadata
            Property(name="tags", data_type=DataType.TEXT_ARRAY,
                     skip_vectorization=True, filterable=True),
            Property(name="skill_level", data_type=DataType.TEXT,
                     skip_vectorization=True, filterable=True),
            Property(name="is_complete_case", data_type=DataType.BOOL,
                     skip_vectorization=True, filterable=True),
        ]
    )

    print("ServiceVlogs collection created successfully!")
```

---

## Retrieval Patterns

### Pattern 1: Find Similar Problems

```python
def find_similar_vlogs(problem_description: str, failure_mode: str = None):
    """Find vlogs with similar problems"""
    query = client.query.get(
        "ServiceVlogs",
        ["vlog_id", "title", "problem_summary", "root_cause", "video_blob_ref"]
    ).with_near_text({
        "concepts": [problem_description]
    })

    if failure_mode:
        query = query.with_where({
            "path": ["failure_modes"],
            "operator": "ContainsAny",
            "valueTextArray": [failure_mode]
        })

    return query.with_limit(5).do()
```

### Pattern 2: Find Vlogs for Current SMIDO Step

```python
def get_vlogs_for_smido_step(smido_step: str, component: str = None):
    """Get example vlogs for current SMIDO step"""
    where_filter = {
        "path": ["smido_steps"],
        "operator": "ContainsAny",
        "valueTextArray": [smido_step]
    }

    if component:
        where_filter = {
            "operator": "And",
            "operands": [
                where_filter,
                {"path": ["components"], "operator": "ContainsAny",
                 "valueTextArray": [component]}
            ]
        }

    return client.query.get(
        "ServiceVlogs",
        ["vlog_id", "title", "solution_summary", "video_blob_ref"]
    ).with_where(where_filter).with_limit(3).do()
```

### Pattern 3: WorldState Matching

```python
def find_vlogs_by_worldstate(world_state_description: str):
    """Find vlogs with similar sensor patterns"""
    return client.query.get(
        "ServiceVlogs",
        ["vlog_id", "title", "world_state_pattern", "typical_sensor_conditions"]
    ).with_near_text({
        "concepts": [world_state_description]
    }).with_limit(5).do()
```

---

## Enrichment Strategy

After Gemini processing, add:

### 1. SMIDO Step Mapping

Use LLM to classify which SMIDO steps are demonstrated:

```python
def classify_smido_steps(vlog_data):
    prompt = f"""
    Based on this vlog:
    Problem: {vlog_data['problem_summary']}
    Steps: {[s['title'] for s in vlog_data['steps']]}
    Root cause: {vlog_data['root_cause']}

    Which SMIDO steps does this demonstrate?
    Options: melding, technisch, installatie_vertrouwd, 3P_power,
             3P_procesinstellingen, 3P_procesparameters, 3P_productinput,
             ketens_onderdelen

    Return JSON array.
    """
    return call_llm(prompt)
```

### 2. Failure Mode Standardization

Map Gemini tags to controlled vocabulary:

```python
FAILURE_MODE_MAPPING = {
    "condensorventilator": "ventilator_defect",
    "warmteafvoer": "te_hoge_temperatuur",
    "hoge condensatiedruk": "hoge_druk",
    # ... etc
}
```

### 3. WorldState Pattern Generation

Create natural language sensor state descriptions:

```python
def generate_worldstate_pattern(vlog_data):
    # Based on root cause and problem, infer likely sensor states
    # Or use LLM to generate from vlog content
    pass
```

---

## Processing Workflow

```
1. Upload .mov files → Gemini 2.5 Pro
   ↓
2. Extract structured data (current format)
   ↓
3. Enrich with:
   - vlog_id, vlog_set extraction
   - SMIDO step classification
   - Failure mode standardization
   - WorldState pattern generation
   - Related clip linking
   ↓
4. Convert to Weaviate format
   ↓
5. Ingest to ServiceVlogs collection
```

---

## Next Steps

1. ✅ Define target structure (this document)
2. ⏳ Process all 15 videos with Gemini
3. ⏳ Create enrichment script
4. ⏳ Implement Weaviate ingestion
5. ⏳ Test retrieval quality
6. ⏳ Integrate with Elysia
