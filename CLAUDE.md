

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

## Data Status - Phase 1 Complete ✅

**All data processed and uploaded to Weaviate**:
- Telemetry: 785K rows → 12 events (VSM_TelemetryEvent)
- Manuals: 689 chunks → 167 sections (VSM_ManualSections), 9 diagrams (VSM_Diagram)
- Vlogs: 15 videos → 15 clips + 5 cases (VSM_VlogClip, VSM_VlogCase)
- Synthetic: 13 snapshots (VSM_WorldStateSnapshot), commissioning data (FD_Assets)

**Processed outputs** in `features/*/output/`:
- `diagrams_metadata.jsonl` (9)
- `manual_sections_classified.jsonl` (167)
- `telemetry_events.jsonl` (12)
- `vlog_clips_enriched.jsonl` (15)
- `vlog_cases_enriched.jsonl` (5)
- `worldstate_snapshots.jsonl` (13)
- `fd_assets_enrichment.json` (Context C)

**See**: [docs/data/PHASE1_COMPLETION_SUMMARY.md](docs/data/PHASE1_COMPLETION_SUMMARY.md)

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

### ✅ Phase 1: COMPLETE (Data Upload)
- **221 objects** in Weaviate (6 VSM collections)
- **13 WorldState snapshots** (reference patterns for AnalyzeSensorPattern)
- **Commissioning data** (Context C for GetAssetHealth)
- **Elysia preprocessing** complete (ELYSIA_METADATA__ has 6 entries)
- **Validation** passed (4 P's, A3 coverage, opgave filtering)
- **Documentation**: [docs/data/PHASE1_COMPLETION_SUMMARY.md](docs/data/PHASE1_COMPLETION_SUMMARY.md)

### 📝 Phase 2: READY (Agent Tools & Tree)
**7 implementation plans** in [docs/plans/](docs/plans/):
1. WorldState Engine + ComputeWorldState tool (2-3h, independent)
2. Simple query tools: GetAlarms, QueryTelemetryEvents, QueryVlogCases (2h, independent)
3. SearchManualsBySMIDO tool (2h, independent)
4. Advanced tools: GetAssetHealth, AnalyzeSensorPattern (3h, depends on #1)
5. SMIDO nodes: M→T→I→D[P1,P2,P3,P4]→O (3h, independent)
6. Orchestrator + Context Manager (4h, depends on #1-5)
7. A3 end-to-end test (2-3h, depends on all)

**Merge strategy**: [docs/plans/00_MERGE_STRATEGY_AND_TESTING.md](docs/plans/00_MERGE_STRATEGY_AND_TESTING.md)  
**Parallelizable**: Plans 1,2,3,5 can run simultaneously (~3h parallel vs ~10h sequential)

---

## Data Storage Strategy

### Weaviate vs Local Files Split

**Weaviate** (221 objects uploaded):
- VSM_ManualSections: 167 (9 opgave flagged)
- VSM_Diagram: 9
- VSM_TelemetryEvent: 12
- VSM_VlogCase: 5
- VSM_VlogClip: 15
- VSM_WorldStateSnapshot: 13 (SYNTHETIC)
- FD_Assets: enriched with Context C (SYNTHETIC)

**Local Files**:
- Telemetry parquet: 785K rows (ComputeWorldState reads directly)
- Manual JSONL: 689 chunks (source data)
- Vlog .mov: 15 videos (playback)

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

## Weaviate Collections - UPLOADED ✅

| Collection | Objects | Status | Purpose |
|------------|---------|--------|---------|
| VSM_ManualSections | 167 | ✅ | SMIDO-filtered search (9 opgave flagged) |
| VSM_Diagram | 9 | ✅ | Visual diagrams for SearchManualsBySMIDO |
| VSM_TelemetryEvent | 12 | ✅ | "Uit balans" incidents |
| VSM_VlogCase | 5 | ✅ | A1-A5 problem→solution workflows |
| VSM_VlogClip | 15 | ✅ | Individual troubleshooting clips |
| VSM_WorldStateSnapshot | 13 | ✅ | Reference patterns (SYNTHETIC) |
| FD_Assets | enriched | ✅ | Context C: commissioning data (SYNTHETIC) |

**All preprocessed**: ELYSIA_METADATA__ has 6 entries

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

## Implementation Roadmap

### ✅ Phase 1: Data Upload - COMPLETE
All collections uploaded, synthetic data generated, preprocessing done. **Ready for Phase 2**.

### 📝 Phase 2: Tools & Tree - IN PROGRESS (7 parallel plans)

**Round 1** (Parallel, ~3h):
- Plan 1: WorldState Engine (`features/telemetry_vsm/src/worldstate_engine.py`)
- Plan 2: Simple tools (GetAlarms, QueryTelemetryEvents, QueryVlogCases in `elysia/api/custom_tools.py`)
- Plan 3: SearchManualsBySMIDO (with opgave filtering, diagram integration)
- Plan 5: SMIDO tree structure (`features/vsm_tree/smido_tree.py`)

**Round 2** (Depends on Plan 1, ~3h):
- Plan 4: GetAssetHealth + AnalyzeSensorPattern (W vs C, pattern matching)

**Round 3** (Integration, ~4h):
- Plan 6: Orchestrator + Context Manager (`features/vsm_tree/`)

**Round 4** (Validation, ~2h):
- Plan 7: A3 end-to-end test (`features/vsm_tree/tests/`, `scripts/demo_a3_scenario.py`)

**Merge order**: 1→2→3→4→5→6→7 (tests after each merge)  
**See**: [docs/plans/00_MERGE_STRATEGY_AND_TESTING.md](docs/plans/00_MERGE_STRATEGY_AND_TESTING.md)

### ⏳ Phase 3: Demo & Polish
- UI enhancements, additional scenarios, documentation

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

## Elysia Patterns (Critical for Phase 2)

### Tree + Branch Creation
```python
from elysia import Tree

tree = Tree(
    branch_initialisation="empty",  # Manual control
    agent_description="Virtual Service Mechanic...",
    style="Professional, clear Dutch",
    end_goal="Root cause identified and solution provided"
)

# Add branches with from_branch_id hierarchy
tree.add_branch(
    branch_id="smido_melding",
    instruction="Collect symptoms, assess urgency...",
    description="Symptom collection phase",
    root=True,  # First branch
    status="Collecting symptoms..."
)

tree.add_branch(
    branch_id="smido_technisch",
    instruction="Visual inspection...",
    description="Quick technical check",
    from_branch_id="smido_melding",  # Comes after M
    status="Performing technical check..."
)
```

### Add Tools to Branches
```python
from elysia.api.custom_tools import compute_worldstate, search_manuals_by_smido

# Add to specific branch
tree.add_tool(compute_worldstate, branch_id="smido_p3_procesparameters")
tree.add_tool(search_manuals_by_smido, branch_id="smido_installatie")
```

## Coding Conventions

### VSM Tool Pattern (Elysia v4)
```python
from elysia import tool, Result, Status

@tool(branch_id="smido_p3_procesparameters")
async def compute_worldstate(
    asset_id: str,
    timestamp: str = None,
    window_minutes: int = 60,
    tree_data=None,  # Auto-injected by Elysia
    **kwargs
):
    """Compute WorldState (W) - 60+ features from parquet."""
    yield Status("Computing WorldState features...")
    
    from features.telemetry_vsm.src.worldstate_engine import WorldStateEngine
    engine = WorldStateEngine("features/telemetry/timeseries_freezerdata/135_1570_cleaned_with_flags.parquet")
    worldstate = engine.compute_worldstate(asset_id, timestamp, window_minutes)
    
    # Store in tree environment
    if tree_data:
        tree_data.environment["worldstate"] = worldstate
    
    yield Result(objects=[worldstate], metadata={"source": "worldstate_engine"})

@tool(branch_id="smido_p2_procesinstellingen")
async def get_asset_health(
    asset_id: str,
    tree_data=None,
    client_manager=None,
    **kwargs
):
    """Compare W vs C - balance check."""
    yield Status("Comparing WorldState vs Context...")
    
    # Get C from FD_Assets, compute W, compare
    # Identify out-of-balance factors
    
    yield Result(objects=[health_summary])

### Weaviate Queries (v4 API)
```python
from elysia.util.client import ClientManager
from weaviate.classes.query import Filter

async def search_manual_by_smido(smido_step: str, query: str):
    """Search manuals filtered by SMIDO step."""
    async with ClientManager().connect_to_async_client() as client:
        collection = client.collections.get("VSM_ManualSections")
        result = await collection.query.hybrid(
            query=query,
            filters=Filter.by_property("smido_step").equal(smido_step) &
                    Filter.by_property("content_type").not_equal("opgave")  # Exclude test content
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

### Phase 2 Implementation (START HERE)
- **Plans Index**: [docs/plans/README.md](docs/plans/README.md) - 7 parallelizable plans
- **Merge Strategy**: [docs/plans/00_MERGE_STRATEGY_AND_TESTING.md](docs/plans/00_MERGE_STRATEGY_AND_TESTING.md)
- **Session Summary**: [docs/plans/SESSION_SUMMARY.md](docs/plans/SESSION_SUMMARY.md)

### Architecture & Data
- **Agent Architecture**: [docs/diagrams/vsm_agent_architecture.mermaid](docs/diagrams/vsm_agent_architecture.mermaid)
- **Phase 1 Complete**: [docs/data/PHASE1_COMPLETION_SUMMARY.md](docs/data/PHASE1_COMPLETION_SUMMARY.md)
- **Weaviate API**: [docs/data/WEAVIATE_API_NOTES.md](docs/data/WEAVIATE_API_NOTES.md) (Filter.by_property patterns)

### Elysia Framework
- **Tool Creation**: [docs/creating_tools.md](docs/creating_tools.md) (@tool decorator, async generators)
- **Basic Usage**: [docs/basic.md](docs/basic.md) (Tree, branches, preprocessing)
- **Elysia Diagrams**: [docs/diagrams/elysia/INDEX.md](docs/diagrams/elysia/INDEX.md) (16 architecture diagrams)
