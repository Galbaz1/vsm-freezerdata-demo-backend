# Weaviate Schema Design: ManualSections

## Overview

This document proposes a Weaviate collection schema for storing parsed manual sections. The schema is designed to support RAG (Retrieval-Augmented Generation) queries from the Elysia agent during troubleshooting sessions.

---

## Collection: `ManualSections`

### Purpose

Store logical sections from the cooling technology manuals, enabling:
1. **SMIDO-step based retrieval** - Get relevant sections for current diagnostic step
2. **Failure mode search** - Find sections related to specific failures
3. **Component-based search** - Retrieve component-specific information
4. **Semantic search** - Natural language queries about troubleshooting

---

## Properties Schema

### Core Identification Properties

| Property | Type | Description | Indexing | Example |
|----------|------|-------------|----------|---------|
| `section_id` | TEXT | Unique identifier for this section | Filterable | `"smido_melding_001"` |
| `manual_id` | TEXT | Source manual identifier | Filterable | `"storingzoeken-koeltechniek_theorie"` |
| `manual_title` | TEXT | Human-readable manual name | Filterable | `"Troubleshooting Cooling Technology"` |
| `chunk_ids` | TEXT[] | Array of chunk UUIDs that comprise this section | None | `["11cdb058-316e-44ba-a0fb-1903707c51e2", ...]` |

### Content Properties

| Property | Type | Description | Indexing | Example |
|----------|------|-------------|----------|---------|
| `title` | TEXT | Section title/heading | Tokenization + Vectorization | `"Melding"` |
| `body_text` | TEXT | Full text content of section | Tokenization + **Vectorization** | `"Is de melding compleet, waar staat..."` |
| `language` | TEXT | Content language | Filterable | `"nl"` or `"en"` |
| `page_start` | INT | Starting page number (0-indexed) | Filterable | `8` |
| `page_end` | INT | Ending page number | Filterable | `10` |
| `page_range` | TEXT | Human-readable page range | None | `"8-10"` |

### Classification Properties

| Property | Type | Description | Indexing | Example |
|----------|------|-------------|----------|---------|
| `smido_step` | TEXT | SMIDO methodology step | Filterable | `"melding"` |
| `smido_steps` | TEXT[] | Multiple SMIDO steps if applicable | Filterable | `["3P_power", "3P_procesinstellingen"]` |
| `content_type` | TEXT | Type of content | Filterable | `"uitleg"`, `"flowchart"`, `"tabel"` |
| `failure_mode` | TEXT | Primary failure mode addressed | Filterable | `"te_hoge_temperatuur"` |
| `failure_modes` | TEXT[] | Multiple failure modes | Filterable | `["ingevroren_verdamper", "slecht_ontdooien"]` |
| `component` | TEXT | Primary component discussed | Filterable | `"verdamper"` |
| `components` | TEXT[] | Multiple components | Filterable | `["compressor", "verdamper", "ventilator"]` |

### Metadata Properties

| Property | Type | Description | Indexing | Example |
|----------|------|-------------|----------|---------|
| `contains_images` | BOOLEAN | Has visual/diagram content | Filterable | `true` |
| `image_descriptions` | TEXT[] | Descriptions of included images | Vectorization | `["Flowchart showing SMIDO steps"]` |
| `contains_table` | BOOLEAN | Has tabular data | Filterable | `true` |
| `is_case_study` | BOOLEAN | Is an example case | Filterable | `true` |
| `case_title` | TEXT | Case study title if applicable | Tokenization | `"Te warm in de trein"` |
| `version` | TEXT | Manual version/date | None | `"20 maart 2018"` |
| `difficulty_level` | TEXT | Technical complexity | Filterable | `"beginner"`, `"intermediate"`, `"advanced"` |

### Derived/Enrichment Properties (Optional, Phase 2)

| Property | Type | Description | Example |
|----------|------|-------------|---------|
| `keywords` | TEXT[] | Extracted keywords | `["temperatuur", "storing", "melding"]` |
| `summary` | TEXT | LLM-generated summary | `"Dit gedeelte beschrijft..."` |
| `related_sensor_columns` | TEXT[] | Telemetry columns mentioned | `["sGekoeldeRuimte", "sHeetgasLeiding"]` |
| `typical_worldstate_pattern` | TEXT | Expected sensor patterns | `"Room temp rising, hot gas low"` |

---

## Vectorization Strategy

### Named Vectors

Weaviate supports multiple named vectors per object. We can use different vectorization strategies:

#### Primary Vector: `content_vector`

- **Source**: `title` + `body_text`
- **Model**: OpenAI `text-embedding-3-small` (or `text-embedding-3-large` for better quality)
- **Dimensions**: 1536 (small) or 3072 (large)
- **Purpose**: General semantic search

#### Secondary Vector: `technical_vector` (Optional, Phase 2)

- **Source**: `body_text` only
- **Model**: Domain-specific embedding (if available) or fine-tuned model
- **Purpose**: Technical terminology matching

### Vectorization Configuration Example

```python
{
  "class": "ManualSections",
  "vectorizer": "text2vec-openai",
  "moduleConfig": {
    "text2vec-openai": {
      "model": "text-embedding-3-small",
      "vectorizeClassName": False,
      "properties": ["title", "body_text"]  # Properties to vectorize
    }
  }
}
```

---

## Property Values and Controlled Vocabularies

### `smido_step` Values

Controlled vocabulary:

```python
SMIDO_STEPS = [
    "melding",                    # Initial report/complaint
    "technisch",                  # Technical quick check
    "installatie_vertrouwd",      # Installation familiarity
    "3P_power",                   # Power checks
    "3P_procesinstellingen",      # Process settings
    "3P_procesparameters",        # Process parameters (measurements)
    "3P_productinput",            # Product/environmental inputs
    "ketens_onderdelen",          # Chains & components isolation
    "koelproces_uit_balans",      # Cooling process imbalance
    "overzicht",                  # Overview/flowchart
    "algemeen"                    # General/foundational
]
```

### `content_type` Values

```python
CONTENT_TYPES = [
    "uitleg",          # Explanation
    "stappenplan",     # Step-by-step procedure
    "flowchart",       # Flowchart/decision tree
    "tabel",           # Table
    "voorbeeldcase",   # Case study
    "diagram",         # Technical diagram
    "foto",            # Photograph
    "schema",          # Schematic
    "checklist",       # Checklist
    "definitie",       # Definition
    "opgave"           # Exercise/assignment (can be filtered out for production)
]
```

### `failure_mode` Values

```python
FAILURE_MODES = [
    "te_hoge_temperatuur",        # High temperature
    "te_lage_temperatuur",        # Low temperature
    "ingevroren_verdamper",       # Frozen evaporator
    "compressor_draait_niet",     # Compressor not running
    "compressor_kortsluiting",    # Compressor short cycling
    "hoge_druk",                  # High pressure
    "lage_druk",                  # Low pressure
    "te_weinig_koudemiddel",      # Insufficient refrigerant
    "te_veel_koudemiddel",        # Excess refrigerant
    "vuile_condensor",            # Dirty condenser
    "vuile_verdamper",            # Dirty evaporator
    "slecht_ontdooien",           # Poor defrost
    "deur_probleem",              # Door issue
    "ventilator_defect",          # Fan defect
    "regelaar_probleem",          # Controller issue
    "sensor_defect",              # Sensor failure
    "lekkage",                    # Refrigerant leak
    "verstopt_filter",            # Clogged filter
    "geen_storing"                # No failure (normal operation explanation)
]
```

### `component` Values

```python
COMPONENTS = [
    "compressor",
    "verdamper",
    "condensor",
    "expansieventiel",
    "ventilator",
    "regelaar",
    "magneetklep",
    "pressostaat",
    "thermostat",
    "vloeistofvat",
    "filter_droger",
    "kijkglas",
    "drukschakelaar",
    "overdrukbeveiliging",
    "ontdooiheater",
    "koudemiddel",
    "systeem_algemeen"  # For general system discussions
]
```

---

## Filterable Queries Examples

### 1. Get sections for a specific SMIDO step

```python
response = client.query.get(
    "ManualSections",
    ["section_id", "title", "body_text", "manual_title"]
).with_where({
    "path": ["smido_step"],
    "operator": "Equal",
    "valueText": "melding"
}).with_limit(10).do()
```

### 2. Search for "high temperature" failure mode

```python
response = client.query.get(
    "ManualSections",
    ["section_id", "title", "body_text"]
).with_where({
    "path": ["failure_modes"],
    "operator": "ContainsAny",
    "valueTextArray": ["te_hoge_temperatuur"]
}).with_limit(10).do()
```

### 3. Get component-specific information (evaporator)

```python
response = client.query.get(
    "ManualSections",
    ["section_id", "title", "body_text"]
).with_where({
    "path": ["components"],
    "operator": "ContainsAny",
    "valueTextArray": ["verdamper"]
}).with_limit(10).do()
```

### 4. Hybrid search: semantic + filters

```python
response = client.query.get(
    "ManualSections",
    ["section_id", "title", "body_text", "smido_step"]
).with_hybrid(
    query="Wat te doen als de compressor niet draait?",
    alpha=0.5  # Balance between vector (0) and keyword (1) search
).with_where({
    "operator": "And",
    "operands": [
        {
            "path": ["smido_step"],
            "operator": "Equal",
            "valueText": "ketens_onderdelen"
        },
        {
            "path": ["components"],
            "operator": "ContainsAny",
            "valueTextArray": ["compressor"]
        }
    ]
}).with_limit(5).do()
```

---

## Sample Data Object

```json
{
  "section_id": "storingzoeken_smido_melding_001",
  "manual_id": "storingzoeken-koeltechniek_theorie",
  "manual_title": "Storingzoeken koeltechniek",
  "chunk_ids": [
    "e9a21e80-0792-4cf3-b85d-ad5d495679e3",
    "2d4466fd-e7a4-41bb-a7e0-8589a888e091"
  ],
  "title": "Melding",
  "body_text": "Is de melding compleet, waar staat de installatie en bij wie moet je zijn?\nIs de melding duidelijk of alleen maar 'hij doet het niet'?\nWelke symptomen zijn er waargenomen door de gebruiker?\nWelke vragen ga je stellen om meer duidelijkheid te krijgen?",
  "language": "nl",
  "page_start": 8,
  "page_end": 8,
  "page_range": "8",
  "smido_step": "melding",
  "smido_steps": ["melding"],
  "content_type": "uitleg",
  "failure_mode": null,
  "failure_modes": [],
  "component": null,
  "components": [],
  "contains_images": false,
  "image_descriptions": [],
  "contains_table": false,
  "is_case_study": false,
  "case_title": null,
  "version": "20 maart 2018",
  "difficulty_level": "beginner"
}
```

---

## Data Ingestion Strategy

### Phase 1: Basic Ingestion

1. **Parse sections** from `.text_chunks.jsonl` files
2. **Group chunks** into logical sections (by heading)
3. **Manual classification**:
   - `smido_step`: Based on heading keywords
   - `content_type`: Based on content markers (table tags, flowchart tags, etc.)
   - `manual_id`, `page_range`: From chunk metadata
4. **Upload to Weaviate** with basic properties

### Phase 2: Enrichment

1. **LLM-based classification**:
   - `failure_modes`: Extract from body_text using GPT-4
   - `components`: Named entity recognition
   - `difficulty_level`: Based on technical terminology density
2. **Cross-referencing**:
   - Link sections that reference each other
   - Identify "related sections"
3. **Summary generation**:
   - Create concise summaries for long sections

### Phase 3: Continuous Improvement

1. **Usage analytics**: Track which sections are most retrieved
2. **User feedback**: Allow Elysia to mark helpful/unhelpful sections
3. **Retraining embeddings**: Fine-tune embeddings on domain data

---

## Weaviate Schema Definition (Python)

```python
import weaviate
from weaviate.classes.config import Configure, Property, DataType

def create_manual_sections_collection(client):
    """Create the ManualSections collection with full schema"""

    client.collections.create(
        name="ManualSections",
        description="Sections from cooling technology manuals for RAG",
        vectorizer_config=Configure.Vectorizer.text2vec_openai(
            model="text-embedding-3-small",
            vectorize_collection_name=False
        ),
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

            # Content
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

            # Classification
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
            Property(name="version", data_type=DataType.TEXT,
                     skip_vectorization=True),
            Property(name="difficulty_level", data_type=DataType.TEXT,
                     skip_vectorization=True, filterable=True),
        ]
    )

    print("ManualSections collection created successfully!")
```

---

## Retrieval Patterns for Elysia

### Pattern 1: SMIDO-Step Aware Retrieval

When the agent is in a specific SMIDO step:

```python
def get_relevant_manual_sections(smido_step: str, query: str, limit: int = 5):
    """Get sections relevant to current SMIDO step"""
    return client.query.get(
        "ManualSections",
        ["title", "body_text", "content_type", "page_range"]
    ).with_hybrid(
        query=query,
        alpha=0.7
    ).with_where({
        "path": ["smido_step"],
        "operator": "Equal",
        "valueText": smido_step
    }).with_limit(limit).do()
```

### Pattern 2: Failure Mode Lookup

When a failure mode is suspected:

```python
def get_failure_mode_guidance(failure_mode: str, smido_step: str = None):
    """Get sections about specific failure mode"""
    where_filter = {
        "path": ["failure_modes"],
        "operator": "ContainsAny",
        "valueTextArray": [failure_mode]
    }

    if smido_step:
        where_filter = {
            "operator": "And",
            "operands": [
                where_filter,
                {"path": ["smido_step"], "operator": "Equal", "valueText": smido_step}
            ]
        }

    return client.query.get(
        "ManualSections",
        ["title", "body_text", "smido_step", "content_type"]
    ).with_where(where_filter).with_limit(10).do()
```

### Pattern 3: Component-Specific Troubleshooting

```python
def get_component_troubleshooting(component: str, query: str):
    """Get troubleshooting info for specific component"""
    return client.query.get(
        "ManualSections",
        ["title", "body_text", "failure_modes"]
    ).with_hybrid(
        query=query,
        alpha=0.6
    ).with_where({
        "path": ["components"],
        "operator": "ContainsAny",
        "valueTextArray": [component]
    }).with_limit(5).do()
```

---

## Index Size Estimation

Given:
- **3 manuals**
- **~110-140 estimated sections**
- **Average section size**: ~300-500 words
- **Vector dimensions**: 1536 (text-embedding-3-small)

**Estimated storage**:
- Text data: ~140 sections × 400 words × 5 bytes/word ≈ **280 KB**
- Vectors: 140 sections × 1536 dimensions × 4 bytes ≈ **860 KB**
- Metadata: ~50 KB
- **Total**: ~**1.2 MB** for manual sections

This is very small and easily manageable in Weaviate.

---

## Alternative Schema Considerations

### Option: Store Chunks Instead of Sections

**Pros**:
- More granular retrieval
- Simpler parsing (no grouping needed)
- Better for pinpoint references

**Cons**:
- More objects (300+ chunks vs ~140 sections)
- May retrieve partial information
- Harder to maintain context

**Recommendation**: Use **sections** for MVP, consider **chunks** for Phase 2 if needed

---

## Next Steps

1. ✅ Design Weaviate schema (this document)
2. ⏳ Implement section parser
3. ⏳ Create ingestion script
4. ⏳ Test with sample data
5. ⏳ Evaluate retrieval quality
6. ⏳ Integrate with Elysia tools
