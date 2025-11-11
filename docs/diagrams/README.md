# SMIDO Methodology Diagrams

This directory contains visual diagrams of the SMIDO troubleshooting methodology for cooling systems.

---

## Files

### Main Documentation
- **`smido_methodology.md`** - Complete documentation with all diagrams embedded in markdown
  - Contains 6 detailed diagrams with explanations
  - Includes legend and color coding
  - Best for reading/reviewing all diagrams together

### Individual Mermaid Diagrams
- **`smido_main_flowchart.mermaid`** - Main SMIDO troubleshooting flow (M→T→I→D→O)
- **`smido_3ps_diagnosis.mermaid`** - Detailed breakdown of Diagnose phase (3 P's + Product Input)
- **`smido_frozen_evaporator_example.mermaid`** - Example troubleshooting workflow for frozen evaporator
- **`smido_data_integration.mermaid`** - How SMIDO integrates with telemetry, manuals, and vlogs

---

## SMIDO Acronym

**SMIDO** = Structured troubleshooting methodology for cooling systems

| Letter | Dutch | English | Description |
|--------|-------|---------|-------------|
| **M** | Melding | Report | Collect symptoms and problem description |
| **T** | Technisch | Technical | Quick visual/auditory inspection for obvious defects |
| **I** | Installatie Vertrouwd | Installation Familiarity | Review system documentation and baseline values |
| **D** | Diagnose | Diagnosis | Systematic diagnosis using **3 P's**: |
|   | | | **P1** - Power (voltage, fuses, current) |
|   | | | **P2** - Procesinstellingen (settings, setpoints) |
|   | | | **P3** - Procesparameters (pressures, temperatures) |
|   | | | **P4** - Productinput (environmental conditions) |
| **O** | Onderdelen | Components | Isolate and test individual components |

---

## Viewing Diagrams

### In Markdown Files
Open `smido_methodology.md` in any markdown viewer that supports mermaid:
- GitHub (renders automatically)
- VS Code with Mermaid extension
- Typora
- Obsidian
- mkdocs (documentation site)

### Individual .mermaid Files
Use tools that support .mermaid files:
- [Mermaid Live Editor](https://mermaid.live/)
- VS Code with Mermaid Preview extension
- Draw.io (import)
- Notion (paste code)

### Export to Images
Use mermaid-cli to export to PNG/SVG:
```bash
# Install mermaid-cli
npm install -g @mermaid-js/mermaid-cli

# Export to PNG
mmdc -i smido_main_flowchart.mermaid -o smido_main_flowchart.png

# Export to SVG
mmdc -i smido_main_flowchart.mermaid -o smido_main_flowchart.svg
```

---

## Color Coding

Diagrams use consistent color coding for SMIDO phases:

| Color | Hex Code | Phase |
|-------|----------|-------|
| 🔵 Light Blue | `#e1f5ff` | **M** - Melding (Report) |
| 🟡 Yellow | `#fff9c4` | **T** - Technisch (Technical) |
| 🟣 Purple | `#f3e5f5` | **I** - Installatie (Familiarity) |
| 🟢 Green | `#e8f5e9` | **D** - Diagnose (3 P's) |
| 🟠 Orange | `#ffe0b2` | **O** - Onderdelen (Components) |
| 🔴 Red | `#ffebee` | Failure/Problem State |
| 🟦 Indigo | `#c5cae9` | Resolution/End State |
| 🟩 Teal | `#e0f2f1` | Data Sources/Tools |

---

## Diagram Details

### 1. Main SMIDO Flowchart
**File**: `smido_main_flowchart.mermaid`

Shows the complete troubleshooting workflow from initial report to resolution, including:
- Decision points at each phase
- Feedback loops for unclear symptoms or unfamiliarity
- Multiple exit points when issues are resolved
- Escalation path to specialist if needed

**Key Features**:
- All 5 SMIDO phases (M→T→I→D→O)
- 3 P's breakdown within Diagnose
- Product Input as 4th P
- Component isolation and system balance checks

---

### 2. 3 P's Diagnosis Detail
**File**: `smido_3ps_diagnosis.mermaid`

Detailed breakdown of the Diagnose (D) phase, showing:
- **P1 - Power**: Electrical checks (voltage, fuses, current)
- **P2 - Procesinstellingen**: Settings checks (thermostat, pressostat, timers, controller)
- **P3 - Procesparameters**: Measurements (pressures, temperatures, superheat, subcooling)
- **P4 - Productinput**: Environmental factors (load, ambient temp, airflow, door frequency)

**Use Case**: When guiding technician through systematic diagnosis

---

### 3. Frozen Evaporator Example
**File**: `smido_frozen_evaporator_example.mermaid`

Real-world troubleshooting example mapping to:
- **Manual**: Page 7 - "Ingevroren verdamper" case
- **Vlog**: A3 - Complete problem-triage-solution workflow
- **Telemetry**: `_flag_main_temp_high`, `_flag_suction_extreme`

**Demonstrates**:
- Full SMIDO methodology in practice
- Integration of all three data sources
- Multiple root causes (defrost timer, dirty ducts, thermostat)
- Verification steps after repair

**Why This Example**: Perfect alignment across manual, vlog, and telemetry data

---

### 4. Data Integration Diagram
**File**: `smido_data_integration.mermaid`

Shows how VSM agent integrates:
- **Telemetry** (785K datapoints) → WorldState features (60+ metrics)
- **Manuals** (3 docs, 922 chunks) → Sections tagged with SMIDO steps
- **Vlogs** (15 clips, 5 cases) → Problem-Triage-Solution phases

**Flow**: Data Sources → Features/Sections/Metadata → Agent Tools → Weaviate Vector DB → Semantic Search → Guidance to Technician

**Use Case**: Understanding VSM system architecture

---

## Related Documentation

- **Manual Structure**: `../data/manuals_structure.md`
- **Telemetry Features**: `../data/telemetry_features.md`
- **Vlog Processing**: `../data/vlogs_processing_results.md`
- **Data Analysis Summary**: `../data/data_analysis_summary.md`
- **Project Overview**: `../../CLAUDE.md`

---

## Usage in VSM Agent

These diagrams are the **conceptual foundation** for:

1. **Decision Tree Implementation** (`elysia/tree/`)
   - Each SMIDO phase maps to tree nodes
   - Decision points become branching logic
   - Tools are called at appropriate phases

2. **Tool Design** (`elysia/tools/`)
   - WorldState tool: Supports M, I, D phases
   - Weaviate query tools: Retrieves manual sections by SMIDO step
   - Component test tools: Supports O phase

3. **Manual Section Tagging** (Weaviate collection)
   - Sections tagged with `smido_step` property
   - Enables semantic search: "Show me Diagnose - Procesinstellingen content"

4. **Demo Scenarios**
   - Frozen evaporator example guides demo flow
   - Shows complete M→T→I→D→O progression
   - Demonstrates data integration

---

## Future Enhancements

Potential additions:
- [ ] Component-specific flowcharts (compressor, evaporator, etc.)
- [ ] Failure mode decision trees
- [ ] Telemetry flag → SMIDO phase mapping diagram
- [ ] Interactive HTML version with clickable nodes
- [ ] Animated sequence diagram showing agent-technician interaction
- [ ] Multi-language versions (English, Dutch)

---

## Contributing

When updating diagrams:
1. Edit the `.mermaid` file directly
2. Update corresponding section in `smido_methodology.md`
3. Test rendering in mermaid live editor
4. Maintain consistent color coding
5. Update this README if adding new diagrams

---

## License

Part of the VSM Freezer Data Demo Backend project. See repository root for license details.

