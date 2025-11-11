

This file provides guidance to the agent when working with code in this repository.

## Project Overview

**Virtual Service Mechanic (VSM) Demo** - An AI agent built on the Elysia framework that helps junior cooling technicians troubleshoot freezer/cooling cell installations using the SMIDO methodology.

**Tech Stack**: Python 3.12.12, FastAPI, DSPy, Weaviate (vector DB), pandas (telemetry analysis)

---

## ⚠️ CRITICAL: Environment Setup

**BEFORE RUNNING ANY PYTHON COMMANDS**, you MUST activate the conda environment:

```bash
source scripts/activate_env.sh
```

**Why:** This repository requires Python 3.12.12 from the `vsm-hva` conda environment. The system may have Python 3.13 or other versions, but this codebase specifically needs 3.12.

**Verification:**
```bash
source scripts/activate_env.sh
python3 --version  # Should show: Python 3.12.12
which python3      # Should point to: .../anaconda3/envs/vsm-hva/bin/python3
```

**Always activate the environment before:**
- Running Python scripts (`python3 scripts/*.py`)
- Running tests (`pytest`)
- Installing packages (`pip install`)
- Running Elysia commands (`elysia start`)

---

### Configuration

All required API keys and configuration are stored in the `.env` file at root of the repository (which may not be visible tot the agent due to security reasons).

### Running Elysia

```bash
# Start the API server
elysia start

# With custom port
elysia start --port 8080

# Access at http://localhost:8000
```

---

## Key Commands

### Data Analysis Scripts

**⚠️ Always activate environment first:**
```bash
source scripts/activate_env.sh
```

Then run scripts:
```bash
# Analyze telemetry parquet files
python3 scripts/analyze_telemetry.py

# Analyze parsed manuals
python3 scripts/analyze_manuals.py

# Process vlogs with Gemini 2.5 Pro
python3 features/vlogs_vsm/src/process_vlogs.py
# Interactive: choose 1 video (test) or all 15 videos

# Preprocess Weaviate collections
python3 scripts/preprocess_collections.py

# Seed test data
python3 scripts/seed_assets_alarms.py
```

### Testing

**⚠️ Always activate environment first:**
```bash
source scripts/activate_env.sh
```

Then run tests:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=elysia

# Run specific test file
pytest tests/test_specific.py

# Run async tests
pytest tests/test_async.py --asyncio-mode=auto
```

### Documentation

```bash
# Serve docs locally
mkdocs serve

# Build docs
mkdocs build
```

---

## Data Status (Updated November 11, 2024)

### ✅ Telemetry Data - READY
- **Location**: `features/telemetry/timeseries_freezerdata/`
- **Files**: `135_1570_cleaned_with_flags.parquet` (785,398 rows, 15 columns)
- **Timespan**: Oct 2022 - Dec 2024 (2.2 years)
- **Sampling**: 1-minute intervals
- **Key columns**: `sGekoeldeRuimte` (room temp), 6 boolean flags
- **Documentation**: [docs/data/telemetry_schema.md](docs/data/telemetry_schema.md)

### ✅ Manuals - READY
- **Location**: `features/extraction/production_output/`
- **Count**: 3 manuals (253 pages total, 689 text chunks, 233 visual chunks)
- **Primary**: `storingzoeken-koeltechniek_theorie_179` (SMIDO methodology, 29 pages, 79 chunks)
- **Other manuals**: 
  - `koelinstallaties-opbouw-en-werking_theorie_2016` (163 pages, 422 chunks)
  - `koelinstallaties-inspectie-en-onderhoud_theorie_168` (61 pages, 188 chunks)
- **Format**: Landing AI parsed (JSON, JSONL, Markdown)
- **Note**: Archive versions in `archive_output/` have 108 pages/300 chunks (older, less complete)
- **Documentation**: [docs/data/manuals_structure.md](docs/data/manuals_structure.md)

### ✅ Vlogs - PROCESSED
- **Location**: `features/vlogs_vsm/` (15 .mov files)
- **Processed**: `features/vlogs_vsm/output/vlogs_vsm_annotations.jsonl`
- **Status**: ALL 15 videos processed + 5 case aggregations (20 total records)
- **Cases**: A1-A5 covering 5 different failure modes
- **Documentation**: [docs/data/vlogs_processing_results.md](docs/data/vlogs_processing_results.md)

**See**: [docs/data/README.md](docs/data/README.md) for complete data analysis overview

---

## Architecture

### Elysia Framework Structure

```
elysia/
├── api/                 # FastAPI application
│   ├── app.py          # Main app
│   ├── cli.py          # Command-line interface
│   └── custom_tools.py # Custom tool definitions
├── core/               # Core agent logic
│   ├── tree.py         # Decision tree implementation
│   └── nodes.py        # Node definitions
├── preprocessing/      # Weaviate collection preprocessing
├── tools/              # Built-in and custom tools
└── util/               # Utilities (client, logging, etc.)
```

### Elysia Architecture Documentation

**Comprehensive low-level diagrams and documentation available:**
- **Start here**: [docs/diagrams/elysia/INDEX.md](docs/diagrams/elysia/INDEX.md) - Complete navigation guide
- **Overview**: [docs/diagrams/elysia/README.md](docs/diagrams/elysia/README.md) - Documentation structure
- **Summary**: [docs/diagrams/elysia/COMPREHENSIVE_SUMMARY.md](docs/diagrams/elysia/COMPREHENSIVE_SUMMARY.md) - 47-page technical deep-dive

**Key diagram topics covered** (16 Mermaid diagrams):
- System architecture and three pillars (decision trees, dynamic display, data awareness)
- Decision tree structure, lifecycle, and recursion control
- Core components: Tree, TreeData, Environment, DecisionNode
- Tool system and Query tool internals
- DSPy integration and multi-model strategy
- Feedback system and few-shot learning
- Collection preprocessing pipeline
- Chunk-on-demand implementation
- FastAPI backend structure

**When to use**: Reference these diagrams when you need to understand Elysia's internals for building VSM-specific tools, designing the SMIDO decision tree, or integrating with telemetry/manuals/vlogs data.

### VSM Domain Diagrams

**Machine-readable SMIDO and troubleshooting logic diagrams:**
- **Start here**: [docs/diagrams/INDEX.md](docs/diagrams/INDEX.md) - Complete catalog of all diagrams
- **Implementation guide**: [docs/diagrams/DIAGRAMS_FOR_AGENT.md](docs/diagrams/DIAGRAMS_FOR_AGENT.md) - Agent integration patterns
- **Detailed catalog**: [docs/diagrams/DIAGRAM_CATALOG.md](docs/diagrams/DIAGRAM_CATALOG.md) - Full metadata for each diagram

**VSM-specific Mermaid diagrams** (9 created, traced to source chunks):
- **SMIDO Methodology** (4): Main flowchart, 3 P's diagnosis, frozen evaporator example, data integration
- **System Fundamentals** (3): Basic refrigeration cycle, instrumentation schema, balance diagram  
- **Troubleshooting Tools** (2): Response template, pressostat adjustment logic

**Key features**:
- Every diagram links to original manual chunk ID (full traceability)
- Indexed by SMIDO phase, failure mode, and components
- Includes agent usage guidance and code examples
- Converted from 233 visual chunks (3.9% selectivity - logic diagrams only)

**When to use**: Reference when implementing SMIDO decision tree, formatting troubleshooting responses, explaining system fundamentals, or guiding technician through diagnosis. Use INDEX.md to find relevant diagrams by SMIDO phase or failure mode.

### VSM-Specific Additions

```
features/
├── telemetry/          # Parquet files with sensor data
├── extraction/         # Parsed manuals (Landing AI output)
└── vlogs_vsm/         # Video annotations (Gemini output)

scripts/
├── analyze_telemetry.py   # Schema analysis
├── analyze_manuals.py     # Manual structure analysis
├── preprocess_collections.py  # Weaviate preprocessing
└── seed_assets_alarms.py  # Test data seeding

docs/data/              # Complete data analysis documentation
├── README.md           # Data overview
├── data_analysis_summary.md  # Executive summary
├── telemetry_*.md      # Telemetry docs
├── manuals_*.md        # Manual docs
└── vlogs_*.md          # Vlog docs
```

---

## SMIDO Methodology

The troubleshooting decision tree follows **SMIDO**:

1. **M**elding - Initial problem report
2. **T**echnisch - Technical quick check (visual inspection)
3. **I**nstallatie vertrouwd - Installation familiarity
4. **D**iagnose (3 P's):
   - **P**ower - Electrical checks
   - **P**rocesinstellingen - Process settings (parameters, setpoints)
   - **P**rocesparameters - Process measurements (temps, pressures)
   - **P**roductinput - Environmental/load conditions
5. **O**nderdelen uitsluiten - Component isolation and repair

**Each Elysia node should map to a SMIDO step** and use appropriate tools/data.

---

## Implementation Status

### ✅ IMPLEMENTED
- **Data Analysis Scripts**: All telemetry, manuals, and vlogs analyzed and documented
- **Vlog Processing**: `features/vlogs_vsm/src/process_vlogs.py` - All 15 videos processed with Gemini 2.5 Pro
- **Basic Collections**: Simple `FD_*` collections exist as MVP (FD_Assets, FD_Alarms via seed scripts)
- **Data Documentation**: Complete analysis in `docs/data/` directory

### 📝 PLANNED (Not Yet Implemented)
- **VSM-Specific Tools**: No `elysia/tools/vsm/` directory exists yet
- **SMIDO Decision Tree**: Tree nodes following SMIDO methodology not implemented
- **WorldState Computation**: Tool for computing 60+ telemetry features not built
- **Rich VSM Collections**: `VSM_ManualSections`, `VSM_TelemetryEvent`, `VSM_VlogCase` collections not created
- **Weaviate Data Import**: No scripts exist to import telemetry events, manual sections, or vlog metadata

### 🔄 IN DESIGN
- **Collection Schemas**: Designed in `docs/data/manuals_weaviate_design.md` and `docs/data/vlogs_structure.md`
- **Data Strategy**: Metadata-vs-raw-data split strategy (see Data Storage Strategy section below)
- **ETL Pipelines**: Event detection, section grouping, and metadata enrichment scripts planned

---

## Data Storage Strategy

### Weaviate vs Local Files Split

**Rationale**: Weaviate is optimized for semantic search and RAG, not for storing massive timeseries or large binary files. Use a hybrid approach:

**Weaviate** (for semantic search, RAG, discovery):
- **VSM_TelemetryEvent**: ~500-1000 event summaries with WorldState features (aggregated metadata)
- **VSM_ManualSections**: ~170-240 logical sections with SMIDO/failure mode tags (grouped chunks)
- **VSM_VlogCase**: 5 aggregated cases with problem-solution workflows
- **VSM_VlogClip**: 15 individual clips with timestamps and components

**Local Files** (for raw data, detail queries, playback):
- **Telemetry parquet**: 785K datapoints (1-min intervals, 2.2 years) - efficient for time-window queries
- **Manual JSONL**: 922 chunks (audit trail, source data)
- **Vlog .mov files**: 15 videos (21.7 MB total, for playback)

### Hybrid Query Pattern

1. **Agent queries Weaviate** for incident discovery and semantic matching
2. **Tool reads parquet** for detailed WorldState computation on-demand
3. **Agent presents combined insights** to user

**Benefits**: Best of both worlds - semantic search + efficient timeseries queries

### Telemetry Strategy
- **Raw timeseries**: Keep in parquet files (785K rows, efficient for time-window queries)
- **Events/Incidents**: In Weaviate as `VSM_TelemetryEvent` - aggregated, semantic, searchable
- **Approach**: Tools query parquet for raw data, Weaviate for incident search

### Manuals Strategy
- **Logical sections**: In Weaviate as `VSM_ManualSections` - grouped, classified, vectorized
- **Source chunks**: Keep in JSONL (reference/audit)
- **Test content**: Include but flag with `content_type="opgave"` for filtering
- **Approach**: Import logical sections, not individual chunks

### Vlogs Strategy
- **Metadata**: In Weaviate as `VSM_VlogCase` and `VSM_VlogClip` - searchable, semantic
- **Videos**: Keep as .mov files locally (21.7 MB total)
- **Approach**: Weaviate for discovery, local files for playback

---

## Weaviate Collections (Target Architecture)

**Note**: Currently, simple `FD_*` collections exist as MVP. The target architecture uses rich `VSM_*` collections:

### VSM_ManualSections
- **Purpose**: Searchable manual sections tagged with SMIDO steps, failure modes, components
- **Schema**: [docs/data/manuals_weaviate_design.md](docs/data/manuals_weaviate_design.md)
- **Size**: ~170-240 sections (grouped from 922 chunks)
- **Status**: 📝 PLANNED

### VSM_TelemetryEvent
- **Purpose**: Historical telemetry incidents with WorldState features (not all 785K rows)
- **Design**: Based on [docs/data/telemetry_features.md](docs/data/telemetry_features.md)
- **Size**: ~500-1000 events (detected from 785K datapoints)
- **Status**: 📝 PLANNED

### VSM_VlogCase
- **Purpose**: Aggregated video cases with problem-triage-solution workflows
- **Schema**: [docs/data/vlogs_structure.md](docs/data/vlogs_structure.md)
- **Size**: 5 cases (A1-A5)
- **Status**: 📝 PLANNED

### VSM_VlogClip
- **Purpose**: Individual video clips with timestamps and components
- **Schema**: [docs/data/vlogs_structure.md](docs/data/vlogs_structure.md)
- **Size**: 15 clips
- **Status**: 📝 PLANNED

---

## WorldState Features

**Proposed**: 60+ features for telemetry analysis, including:
- Current state (latest sensor values)
- Trends (30min, 2hr, 24hr windows)
- Incident flags (derived from raw flags)
- Health scores (cooling performance, compressor health, etc.)

**Full spec**: [docs/data/telemetry_features.md](docs/data/telemetry_features.md)

---

## Demo Scenarios

**⭐ PRIMARY RECOMMENDED SCENARIO: A3 "Ingevroren Verdamper" (Frozen Evaporator)**

This is the **best case scenario** with perfect alignment across ALL data sources (manual + vlog + telemetry). All development and demo efforts should prioritize this scenario.

### Recommended: A3 "Ingevroren Verdamper" (Frozen Evaporator) ⭐ PRIMARY
- **Manual**: Explicit case on page ~7 with photo + "Koelproces uit balans" section
- **Vlog**: Perfect match with A3_1, A3_2, A3_3 (complete problem-triage-solution workflow)
- **Telemetry**: Flags: `_flag_main_temp_high`, `_flag_suction_extreme`
- **SMIDO**: Complete M→T→I→D→O flow (full methodology coverage)
- **Why**: Perfect alignment across all data sources - the star case for demo
- **Problem**: Koelcel bereikt temperatuur niet, verdamper volledig bevroren
- **Root cause**: Defrost cycle malfunction + vervuilde luchtkanalen
- **Solution**: Manual defrost + clean air ducts + calibrate thermostat

### Alternative: A1 "Condensor Ventilator" (Condenser Fan)
- **Problem**: Pressostaat + electrical connection issue
- **Good for**: Demonstrating 3P-Procesinstellingen (settings check)

---

## Next Development Steps

### Phase 1: Data Import to Weaviate (Priority)
**Goal**: Import telemetry events, manual sections, and vlog metadata into VSM_* collections

1. **Telemetry Event Detection** (`features/telemetry_vsm/src/detect_events.py`)
   - Detect incidents from flags (_flag_main_temp_high, etc.)
   - Compute WorldState features per event
   - Output JSONL with event metadata (~500-1000 events)

2. **Manual Section Grouping** (`features/manuals_vsm/src/parse_sections.py`)
   - Group chunks into logical sections
   - Detect and flag test content (`content_type="opgave"`)
   - Classify SMIDO steps and failure modes

3. **Vlog Metadata Enrichment** (`features/vlogs_vsm/src/enrich_vlog_metadata.py`)
   - Add SMIDO step tags
   - Standardize failure modes
   - Generate sensor pattern mappings

4. **Weaviate Import Scripts**
   - Create VSM_* collection schemas
   - Import enriched data
   - Verify collections are queryable

### Phase 2: Elysia Tools (After data import)
- WorldState computation tool (reads parquet, computes 60+ features)
- Weaviate query tools (by SMIDO step, failure mode, component)
- SMIDO decision tree nodes

### Phase 3: Demo Flow
- **PRIMARY**: Test with A3 "Ingevroren Verdamper" (Frozen Evaporator) scenario ⭐
  - This is the best case scenario with perfect data alignment
  - Verify end-to-end workflow: manual + vlog + telemetry integration
  - Test complete SMIDO flow (M→T→I→D→O)
- Polish and document

**See**: `todo.md` for detailed implementation tasks

---

## Important File Locations

### Configuration
- `.env` - Environment variables (API keys, Weaviate connection)
- `pyproject.toml` - Python package config
- `mkdocs.yml` - Documentation config

### Data
- `features/telemetry/timeseries_freezerdata/135_1570_cleaned_with_flags.parquet`
- `features/extraction/production_output/storingzoeken-koeltechniek_theorie_179/*.jsonl`
- `features/vlogs_vsm/output/vlogs_vsm_annotations.jsonl`

### Documentation
- `docs/data/` - Complete data analysis (telemetry, manuals, vlogs)
- `docs/data/README.md` - Start here for data overview
- `docs/data/data_analysis_summary.md` - Answers all analysis questions

### Scripts
- `scripts/analyze_*.py` - Data analysis utilities
- `features/vlogs_vsm/src/process_vlogs.py` - Vlog processing with Gemini

---

## Coding Conventions

### Tool Definition
```python
from elysia import tool, Tree

tree = Tree()

@tool(tree=tree)
async def query_worldstate(asset_id: str, timestamp: str) -> dict:
    """Compute WorldState features for troubleshooting."""
    # Load telemetry from parquet
    # Compute features
    # Return structured dict
    pass
```

### Weaviate Queries
```python
from elysia.util.client import ClientManager

async def search_manual_by_smido(smido_step: str, query: str):
    """Search manuals filtered by SMIDO step."""
    async with ClientManager().connect_to_client() as client:
        result = client.collections.get("VSM_ManualSections").query.hybrid(
            query=query,
            filters={"path": ["smido_step"], "operator": "Equal",
                     "valueText": smido_step}
        )
        return result
```

### Tool Construction Pattern (Example Reference)
**Note**: These are example patterns from archived docs. Actual VSM tools not yet implemented.

```python
# Example: WorldState computation tool (PLANNED)
from elysia import tool, Tree
import pandas as pd

tree = Tree()

@tool(tree=tree)
async def compute_worldstate(asset_id: str, timestamp: str, window_minutes: int = 60) -> dict:
    """
    Compute WorldState features for troubleshooting.
    Reads from parquet file (not Weaviate) for efficiency.
    """
    # Load telemetry from parquet
    df = pd.read_parquet('features/telemetry/timeseries_freezerdata/135_1570_cleaned_with_flags.parquet')
    
    # Filter time window
    # Compute 60+ features (current state, trends, health scores)
    # Return structured dict
    
    return {
        "current_state": {...},
        "trends": {...},
        "health_scores": {...}
    }
```

### Async/Await
- All tools should be `async def`
- Use `await` for I/O operations (Weaviate, file reads)
- FastAPI endpoints are `async`

---

## Troubleshooting

### Vlog Processing Issues
```bash
# If Gemini fails: check API key in .env
export GOOGLE_API_KEY="your-key"

# Run with limit for testing
python features/vlogs_vsm/src/process_vlogs.py --limit 1
```

### Weaviate Connection
```bash
# Check .env has correct credentials
# WCD_URL should be full URL (https://...)
# Test connection:
python -c "from elysia.util.client import ClientManager; ClientManager().connect_to_client()"
```

### Telemetry Analysis
```python
# Quick parquet inspection
import pandas as pd
df = pd.read_parquet("features/telemetry/timeseries_freezerdata/135_1570_cleaned_with_flags.parquet")
print(df.dtypes)
print(df.describe())
```

---

## Reference Documentation

- **Elysia Docs**: https://weaviate.github.io/elysia/
- **Weaviate Docs**: https://weaviate.io/developers/weaviate
- **DSPy Docs**: https://dspy-docs.vercel.app/
- **Data Analysis**: [docs/data/README.md](docs/data/README.md)
