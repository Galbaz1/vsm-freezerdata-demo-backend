# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Virtual Service Mechanic (VSM) Demo** - An AI agent built on the Elysia framework that helps junior cooling technicians troubleshoot freezer/cooling cell installations using the SMIDO methodology.

**Tech Stack**: Python 3.11-3.12, FastAPI, DSPy, Weaviate (vector DB), pandas (telemetry analysis)

---

## Development Setup

### Environment

```bash
# Using conda (recommended)
conda create -n vsm-hva python=3.12
conda activate vsm-hva
pip install -e .

# Or using venv
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Configuration

Copy `.env.example` to `.env` and configure:
- `WCD_URL` and `WCD_API_KEY` - Weaviate Cloud cluster
- `GOOGLE_API_KEY` - For Gemini (vlog processing)
- `OPENAI_API_KEY` or `OPENROUTER_API_KEY` - For LLM models
- Model configuration: `BASE_MODEL`, `COMPLEX_MODEL`, providers

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

```bash
# Analyze telemetry parquet files
python scripts/analyze_telemetry.py

# Analyze parsed manuals
python scripts/analyze_manuals.py

# Process vlogs with Gemini 2.5 Pro
python features/vlogs_vsm/src/process_vlogs.py
# Interactive: choose 1 video (test) or all 15 videos

# Preprocess Weaviate collections
python scripts/preprocess_collections.py

# Seed test data
python scripts/seed_assets_alarms.py
```

### Testing

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
- **Count**: 3 manuals (108 pages total, ~300 chunks)
- **Primary**: `storingzoeken-koeltechniek_theorie` (SMIDO methodology)
- **Format**: Landing AI parsed (JSON, JSONL, Markdown)
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

## Weaviate Collections (Planned)

### ManualSections
- **Purpose**: Searchable manual sections tagged with SMIDO steps, failure modes, components
- **Schema**: [docs/data/manuals_weaviate_design.md](docs/data/manuals_weaviate_design.md)
- **Size**: ~110-140 sections

### ServiceVlogs
- **Purpose**: Video metadata with problem-triage-solution workflows
- **Schema**: [docs/data/vlogs_structure.md](docs/data/vlogs_structure.md)
- **Size**: 5 cases (A1-A5) + 15 individual clips

### Incidents
- **Purpose**: Historical telemetry incidents with WorldState features
- **Design**: Based on [docs/data/telemetry_features.md](docs/data/telemetry_features.md)
- **Size**: ~500-1000 incidents

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

### Recommended: A3 "Ingevroren Verdamper" (Frozen Evaporator)
- **Manual**: Explicit case on page ~7 with photo
- **Vlog**: Perfect match with A3_1, A3_2, A3_3
- **Telemetry**: `_flag_main_temp_high`, `_flag_suction_extreme`
- **SMIDO**: Complete M→T→I→D→O flow
- **Why**: Perfect alignment across all data sources

### Alternative: A1 "Condensor Ventilator" (Condenser Fan)
- **Problem**: Pressostaat + electrical connection issue
- **Good for**: Demonstrating 3P-Procesinstellingen (settings check)

---

## Next Development Steps

### Phase 1: Vlog Metadata Enrichment (2-3 days)
```bash
# Create enrichment script to:
# - Map Dutch tags to controlled vocabularies
# - Add SMIDO step tags
# - Add sensor pattern mappings
# - Link A3 to "Ingevroren verdamper" manual section
```

### Phase 2: Weaviate Collections (2-3 days)
```python
# Implement collection schemas
from elysia.util.client import ClientManager

# Create ManualSections collection
# Create ServiceVlogs collection
# Create Incidents collection
```

### Phase 3: ETL Pipelines (3-5 days)
- Manual section parsing (group chunks → sections)
- Incident detection (telemetry → incidents with WorldState)
- Vlog enrichment integration

### Phase 4: Elysia Integration (5-7 days)
- WorldState computation tool
- Weaviate query tools (by SMIDO step, failure mode, component)
- SMIDO decision tree nodes
- Demo flow implementation

**Total to working demo**: ~2 weeks

---

## Important File Locations

### Configuration
- `.env` - Environment variables (API keys, Weaviate connection)
- `pyproject.toml` - Python package config
- `mkdocs.yml` - Documentation config

### Data
- `features/telemetry/timeseries_freezerdata/135_1570_cleaned_with_flags.parquet`
- `features/extraction/production_output/storingzoeken-koeltechniek_theorie/*.jsonl`
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
        result = client.collections.get("ManualSections").query.hybrid(
            query=query,
            filters={"path": ["smido_step"], "operator": "Equal",
                     "valueText": smido_step}
        )
        return result
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
