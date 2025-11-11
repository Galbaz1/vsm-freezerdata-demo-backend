

This file provides guidance to the agent when working with code in this repository.

## Project Overview

**Virtual Service Mechanic (VSM) Demo** - An AI agent built on the Elysia framework that helps junior cooling technicians troubleshoot freezer/cooling cell installations using the SMIDO methodology.

**Tech Stack**: Python 3.12.12, FastAPI, DSPy, Weaviate (vector DB), pandas (telemetry analysis), Next.js 14 (frontend)

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
# Start the API server (includes frontend)
elysia start

# With custom port
elysia start --port 8080

# Access at http://localhost:8000
```

**Frontend Development:**

The Elysia frontend source code is located in `apps/elysia-frontend/`. To develop or customize the frontend:

```bash
cd apps/elysia-frontend
npm install          # First time setup
npm run dev          # Development server (http://localhost:3000)

# Build and copy to backend
npm run assemble     # Builds and copies to ../../elysia/api/static/
```

See `apps/elysia-frontend/README_VSM.md` for detailed frontend setup and VSM customization guide.

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

The troubleshooting decision tree follows **SMIDO** (M→T→I→D→O):

1. **M**elding - Symptom collection, urgency assessment
2. **T**echnisch - Visual/audio inspection, quick checks
3. **I**nstallatie vertrouwd - Familiarity check, schemas, design parameters
4. **D**iagnose - **4 P's** (manual says "3-P's" but lists 4):
   - **P1** Power - Electrical supply checks
   - **P2** Procesinstellingen - Settings vs design (pressostaat, defrost, thermostat)
   - **P3** Procesparameters - Measurements vs design (temps, pressures)
   - **P4** Productinput - External conditions vs design (ambient, product load, door usage)
5. **O**nderdelen uitsluiten - Component isolation (chains, wiring)

**Key Concept**: **"Uit balans"** (out of balance) - faults aren't always broken components, system can operate outside design parameters.

**Each DecisionNode maps to SMIDO step** with specific tools and W/C data access.

---

## Implementation Status

### ✅ IMPLEMENTED
- Data analysis, vlog processing (15 videos), FD_* test collections
- Architecture design: [docs/diagrams/vsm_agent_architecture.mermaid](docs/diagrams/vsm_agent_architecture.mermaid)
- Data strategy: [docs/data/DATA_UPLOAD_STRATEGY.md](docs/data/DATA_UPLOAD_STRATEGY.md)

### 📝 PLANNED (Priority Order)
1. **Upload Core Collections**: VSM_ManualSections, VSM_Diagram, VSM_TelemetryEvent, VSM_VlogCase/Clip
2. **Generate Synthetic**: VSM_WorldStateSnapshot (8-12 patterns), enrich FD_Assets with C
3. **Elysia Preprocessing**: Run `preprocess()` on all VSM_* collections
4. **Build 7 VSM Tools**: ComputeWorldState, QueryTelemetryEvents, SearchManualsBySMIDO, QueryVlogCases, GetAlarms, GetAssetHealth, AnalyzeSensorPattern
5. **SMIDO Decision Tree**: M→T→I→D[P1,P2,P3,P4]→O nodes with tool mappings

---

## Data Storage Strategy

### Weaviate vs Local Files Split

**Rationale**: Weaviate is optimized for semantic search and RAG, not for storing massive timeseries or large binary files. Use a hybrid approach:

**Weaviate** (semantic search, RAG):
- **VSM_ManualSections** + **VSM_Diagram**: ~240 sections + 9 diagrams (SMIDO-tagged)
- **VSM_TelemetryEvent**: ~1000 "uit balans" incidents (aggregated from 785K rows)
- **VSM_VlogCase** + **VSM_VlogClip**: 5 cases + 15 clips (problem→solution)
- **VSM_WorldStateSnapshot**: 8-12 reference patterns (SYNTHETIC - balance factors)
- **FD_Assets** (enriched): Commissioning data (C) for balance checks (SYNTHETIC)

**Local Files** (raw data, on-demand computation):
- **Telemetry parquet**: 785K rows → ComputeWorldState tool
- **Manual JSONL**: 922 chunks (audit)
- **Vlog .mov**: 15 videos (playback)

### Hybrid Query Pattern

1. **Agent queries Weaviate** for semantic discovery (incidents, manuals, vlogs, patterns)
2. **Tool reads parquet** for WorldState (W) computation on-demand
3. **Agent compares W vs C** (commissioning data from FD_Assets) - balance check
4. **Agent presents insights**: "System uit balans" or "Component defect"

**Benefits**: Semantic search (Weaviate) + time-series efficiency (parquet) + balance analysis (W vs C)

### Data Strategy by Tool Need

**ComputeWorldState** (P3 node):
- Reads parquet directly (785K rows) → computes W on-demand
- Not in Weaviate (too large, inefficient for time-series)

**SearchManualsBySMIDO** (I, P2, O nodes):
- Queries VSM_ManualSections + VSM_Diagram
- Returns text sections + visual diagrams filtered by SMIDO step
- Test content flagged `content_type="opgave"` (filterable)

**QueryVlogCases** (O node):
- Queries VSM_VlogCase/Clip for similar problem→solution workflows
- .mov files local (playback reference)

**GetAssetHealth** (M, T, P2 nodes):
- Needs C (commissioning data) from enriched FD_Assets
- Compares W vs C → balance check ("uit balans" detection)

**AnalyzeSensorPattern** (P3, P4 nodes):
- Queries VSM_WorldStateSnapshot (synthetic reference patterns)
- Compares current W against typical "uit balans" patterns

---

## Weaviate Collections (Target Architecture)

**Note**: `FD_*` collections (FD_Assets, FD_Alarms, FD_Cases) exist as MVP test data. VSM_* collections are production.

### VSM_ManualSections (~240 sections)
- SMIDO-tagged sections + diagrams for SearchManualsBySMIDO tool
- Grouped from 922 chunks, filterable by SMIDO step/failure mode/component

### VSM_TelemetryEvent (~1000 events)
- Aggregated incidents (not 785K rows) with WorldState metadata
- Represents "uit balans" states, not just broken components

### VSM_VlogCase (5 cases) + VSM_VlogClip (15 clips)
- Problem→Solution workflows for QueryVlogCases tool
- SMIDO-tagged, linked to manual sections

### VSM_Diagram (9 diagrams)
- Mermaid logic diagrams returned by SearchManualsBySMIDO
- Linked to manual sections via chunk_id

### VSM_WorldStateSnapshot (8-12 patterns) - SYNTHETIC
- Reference patterns for AnalyzeSensorPattern tool
- Typical W for each "uit balans" scenario (balance factors from manual page 11)

### FD_Assets (enriched) - SYNTHETIC CONTEXT
- Installation commissioning data ("gegevens bij inbedrijfstelling")
- Design parameters (C) for GetAssetHealth to compare against WorldState (W)

---

## WorldState (W) vs Context (C)

**WorldState (W)** - Dynamic state (changes during troubleshooting):
- Current sensor readings (ComputeWorldState tool → parquet)
- Technician observations (visual, audio, tactile)
- Customer symptoms, urgency (goods at risk)
- 60+ computed features (trends, flags, health scores)

**Context (C)** - Static design/historical data:
- Commissioning data ("gegevens bij inbedrijfstelling") - stored in FD_Assets
- Design parameters (target temps, pressures, superheat, subcooling)
- Component capacities (compressor, evaporator, condenser matched)
- Control settings (pressostat cutouts, defrost intervals)
- Schemas, service history

**Balance Check**: GetAssetHealth compares W vs C to detect "uit balans" (operating outside design parameters).

**Full spec**: [docs/data/telemetry_features.md](docs/data/telemetry_features.md), [docs/data/DATA_UPLOAD_STRATEGY.md](docs/data/DATA_UPLOAD_STRATEGY.md)

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
- **Good for**: Demonstrating P2-Procesinstellingen (settings check) and P4-Productinput (condenser conditions)

---

## Next Development Steps

### Phase 1: Core Collections (Real Data)
1. **Diagrams + Manual Sections** (`features/diagrams_vsm/`, `features/manuals_vsm/`)
   - Extract Mermaid metadata, group chunks into sections
   - Classify SMIDO steps (4 P's!), failure modes, components
   
2. **Telemetry Events** (`features/telemetry_vsm/src/detect_events.py`)
   - Detect "uit balans" incidents from flags
   - Compute WorldState features per event (~500-1000 events)

3. **Vlog Enrichment** (`features/vlogs_vsm/src/enrich_vlog_metadata.py`)
   - Add SMIDO tags, standardize failure modes
   - Generate WorldState patterns

### Phase 2: Synthetic Data (Agent References)
1. **WorldState Snapshots** (`features/telemetry_vsm/src/generate_worldstate_snapshots.py`)
   - 8-12 reference patterns from vlogs + manual balance factors (page 11)
   - Required by AnalyzeSensorPattern tool

2. **Enrich FD_Assets** (`features/integration_vsm/src/enrich_fd_assets.py`)
   - Add commissioning data (C): design temps, pressures, control settings
   - Required by GetAssetHealth tool for W vs C comparison

### Phase 3: Integration
- Cross-collection linking, Elysia preprocessing, validation

### Phase 4: Agent Tools & Tree
- **Build 7 VSM tools**: ComputeWorldState, QueryTelemetryEvents, SearchManualsBySMIDO, QueryVlogCases, GetAlarms, GetAssetHealth, AnalyzeSensorPattern
- **SMIDO Tree**: M→T→I→D[P1,P2,P3,P4]→O nodes with tool mappings

### Phase 5: Demo & Validation
- **PRIMARY**: Test with A3 "Ingevroren Verdamper" scenario ⭐
- Verify W vs C balance checks, pattern matching, cross-collection linking
- Polish and document

**See**: [docs/data/DATA_UPLOAD_STRATEGY.md](docs/data/DATA_UPLOAD_STRATEGY.md) for detailed upload plan

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

### Agent Tool Pattern
```python
from elysia import tool, Tree

tree = Tree()

@tool(tree=tree, branch_id="smido_diagnose")
async def compute_worldstate(asset_id: str, timestamp: str, window_minutes: int = 60) -> dict:
    """Compute WorldState (W) from parquet for SMIDO diagnosis."""
    # Load telemetry, compute 60+ features
    # Returns W (current state, trends, flags, health scores)
    pass

@tool(tree=tree, branch_id="smido_diagnose")
async def get_asset_health(asset_id: str) -> dict:
    """Compare WorldState (W) vs Context (C) - balance check."""
    # Get C from FD_Assets (commissioning data)
    # Get W from ComputeWorldState
    # Compare: is system "uit balans"?
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

### VSM Tool → Data Mapping

| Tool | Weaviate | Parquet | Synthetic | SMIDO Node |
|------|----------|---------|-----------|------------|
| ComputeWorldState | - | ✓ | - | P3 |
| QueryTelemetryEvents | VSM_TelemetryEvent | - | - | P4, O |
| SearchManualsBySMIDO | VSM_ManualSections, VSM_Diagram | - | - | I, P2, O |
| QueryVlogCases | VSM_VlogCase, VSM_VlogClip | - | - | O |
| GetAlarms | VSM_TelemetryEvent | - | - | M, P1 |
| GetAssetHealth | VSM_TelemetryEvent | ✓ | FD_Assets (C) | M, T, P2 |
| AnalyzeSensorPattern | VSM_WorldStateSnapshot | ✓ | Snapshots | P3, P4 |

**W = WorldState** (dynamic), **C = Context** (static design data)

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

## Key Documentation

### Architecture & Strategy
- **Agent Architecture**: [docs/diagrams/vsm_agent_architecture.mermaid](docs/diagrams/vsm_agent_architecture.mermaid)
- **Data Upload**: [docs/data/DATA_UPLOAD_STRATEGY.md](docs/data/DATA_UPLOAD_STRATEGY.md)
- **Synthetic Data**: [docs/data/SYNTHETIC_DATA_STRATEGY.md](docs/data/SYNTHETIC_DATA_STRATEGY.md)

### Data Analysis
- **Overview**: [docs/data/README.md](docs/data/README.md)
- **Summary**: [docs/data/data_analysis_summary.md](docs/data/data_analysis_summary.md)
- **Schemas**: telemetry_features.md, manuals_weaviate_design.md, vlogs_structure.md

### Framework Docs
- **Elysia**: https://weaviate.github.io/elysia/
- **Elysia Diagrams**: [docs/diagrams/elysia/INDEX.md](docs/diagrams/elysia/INDEX.md)
- **Weaviate**: https://weaviate.io/developers/weaviate
