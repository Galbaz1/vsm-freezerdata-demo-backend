# Visual Chunks Analysis for Mermaid Conversion

**Purpose**: Identify which manual diagrams should be recreated in Mermaid format for optimal VSM agent understanding.

**Analysis Date**: November 11, 2024

---

## Selection Criteria for Mermaid Conversion

### ✅ INCLUDE - High Value for Agent
1. **Flowcharts** - Sequential decision logic (direct mapping to agent tree)
2. **Process flows** - System operation workflows
3. **Troubleshooting tables** - Symptom → Cause → Solution mappings
4. **Component relationships** - How parts interact
5. **State transitions** - System behavior changes
6. **Control logic** - Regulatory mechanisms

### ❌ EXCLUDE - Low Value for Mermaid
1. **Photographs** - Better kept as images (visual inspection reference)
2. **P-h diagrams** - Complex thermodynamic charts (keep as images)
3. **Equipment labels** - Product specs (keep as images)
4. **Logos** - Branding (not relevant for troubleshooting)
5. **Safety signs** - Visual symbols (keep as images)

---

## Manual 1: Troubleshooting (`storingzoeken-koeltechniek_theorie_179`)

### 🔥 PRIORITY 1 - Critical for Agent Logic

#### 1. SMIDO Attack Plan Flowchart
**Chunk ID**: `55a1e55e-41af-47d2-8f3e-6453dc49c84d`
**Page**: 7 (page-008)
**Type**: Flowchart
**Description**: Complete SMIDO troubleshooting methodology flowchart

**Agent Value**: ⭐⭐⭐⭐⭐ CRITICAL
- Direct mapping to agent decision tree nodes
- Shows all decision points and feedback loops
- Contains M→T→I→D→O progression
- Includes "Informeren" and "Diagnose" phases

**Mermaid Advantages**:
- Machine-readable decision logic
- Easy to parse conditions and branches
- Can auto-generate agent tree nodes
- Version-controllable

**Status**: ✅ ALREADY CREATED (`smido_main_flowchart.mermaid`)

---

#### 2. Balance Diagram (Koelproces uit balans)
**Chunk ID**: `4806fb93-38a9-43bb-a3bf-33e32c837581`
**Page**: 11 (page-012)
**Type**: Balance scale diagram
**Description**: Shows components vs. factors affecting cooling balance

**Agent Value**: ⭐⭐⭐⭐ HIGH
- Illustrates system equilibrium concept
- Left side: Components (EXPANSIEORGAAN, VERDAMPER, COMPRESSOR, CONDENSOR)
- Right side: Factors (Koudemiddel hoeveelheid, Koellast product, etc.)
- Shows "Onderlinge relatie" (interrelationships)

**Mermaid Advantages**:
- Can represent as bidirectional graph
- Shows component-factor relationships
- Useful for "Koelproces uit balans" diagnostic step

**Status**: ⏳ NEEDS CREATION

---

#### 3. Troubleshooting Table Structure
**Chunk ID**: `9e024d44-bc1b-4a36-b7a8-eec8614a838f`
**Page**: 22 (page-023)
**Type**: Flowchart
**Description**: Structure of troubleshooting table (Symptoms → Causes → Solutions)

**Agent Value**: ⭐⭐⭐⭐ HIGH
- Shows diagnostic reasoning flow
- Maps to agent tool outputs
- Template for troubleshooting responses

**Mermaid Advantages**:
- Simple 3-step linear flow
- Can template agent response format
- Easy to understand

**Status**: ⏳ NEEDS CREATION

---

### 🟡 PRIORITY 2 - Useful Context

#### 4. Refrigeration Cycle Diagram (with temps/pressures)
**Chunk ID**: `bccc26fd-330d-45ba-b990-ddc0d10b101b`
**Page**: 12 (page-013)
**Type**: Labeled diagram
**Description**: Refrigeration cycle with R134a, showing temps and pressures

**Agent Value**: ⭐⭐⭐ MEDIUM
- Shows expected system states
- Good for "Installatie Vertrouwd" phase
- Reference for normal operation

**Mermaid Advantages**:
- Can represent as graph with labeled edges
- Shows state transitions
- Useful for comparison with telemetry

**Status**: ⏳ CONSIDER CREATION

---

### ⚪ PRIORITY 3 - Keep as Images

#### Photos (Not for Mermaid)
- `d17a0b0b-6ed0-4e75-8094-36b64a2aa361` - Frozen evaporator photo (keep as image)
- `aa4b26ca-91f6-4265-82da-7422c05531ca` - Train photo (keep as image)
- `d33d47c6-a9c6-41fa-9ec3-f06aa3c855d7` - Coolworld mobile unit (keep as image)

#### Complex Charts (Not for Mermaid)
- `9405108c-e266-4489-9a7b-91bfd0254551` - P-h diagram (keep as image)

---

## Manual 2: Structure & Operation (`koelinstallaties-opbouw-en-werking_theorie_2016`)

### 🔥 PRIORITY 1 - Critical for Agent Understanding

#### 5. Basic Refrigeration Cycle (Simple)
**Chunk ID**: `e91e4028-a83e-48a3-8798-ba7d216ad2cd`
**Page**: 8 (page-009)
**Type**: Cycle diagram
**Description**: 4 components in circular flow (Compressor → Condensor → Capillair → Verdamper)

**Agent Value**: ⭐⭐⭐⭐⭐ CRITICAL
- Fundamental system understanding
- Shows component sequence
- High/low pressure zones
- Foundation for "Installatie Vertrouwd" phase

**Mermaid Advantages**:
- Simple 4-node cycle
- Clear flow direction
- Easy to annotate with states
- Good educational value

**Status**: ⏳ NEEDS CREATION

---

#### 6. Schematic Cooling Installation
**Chunk ID**: `6c631446-7f65-475e-8df0-8109a44e85f9`
**Page**: 8 (page-009)
**Type**: Schematic diagram
**Description**: Complete system with P/T measurements, heat flows

**Agent Value**: ⭐⭐⭐⭐ HIGH
- Shows instrumentation (P and T sensors)
- Heat flows labeled
- Pressure/state zones
- Good for "3 P's - Procesparameters" phase

**Mermaid Advantages**:
- Can show measurement points
- Annotate with expected values
- Useful for sensor-based diagnostics

**Status**: ⏳ NEEDS CREATION

---

### 🟡 PRIORITY 2 - Useful for Specific Cases

#### 7. Multiple Evaporator System
**Chunk ID**: `2d32a8ed-630c-4e5f-968a-f2eba21ac5b6`
**Page**: 136 (page-137)
**Type**: System schematic
**Description**: Multi-temperature evaporator system (-10°C, -5°C, 0°C)

**Agent Value**: ⭐⭐⭐ MEDIUM
- Shows complex system configuration
- Pressure regulation at different temps
- Useful for advanced diagnostics

**Mermaid Advantages**:
- Can simplify complex P&ID
- Show control logic clearly
- Good for multi-zone systems

**Status**: ⏳ CONSIDER CREATION

---

#### 8. Hot Gas Defrost System
**Chunk ID**: `424a4dc3-637e-45f1-9b3b-3554ae466b42`
**Page**: 113 (page-114)
**Type**: System schematic
**Description**: 3 evaporators with hot gas defrost valves

**Agent Value**: ⭐⭐⭐ MEDIUM
- Relevant for frozen evaporator case (A3)
- Shows defrost logic
- Valve sequencing

**Mermaid Advantages**:
- Can show valve states (open/closed)
- Simplify complex P&ID
- Useful for defrost troubleshooting

**Status**: ⏳ CONSIDER CREATION

---

### ⚪ PRIORITY 3 - Keep as Images

#### Photos/Equipment
- `a4c4788d-191a-4a4b-9ce5-1c40297c8b59` - Refrigerator photo (keep)
- `2eb707ae-2347-4968-9477-58d7eddce642` - Training unit photo (keep)
- All P-h diagrams (too complex for Mermaid)

---

## Manual 3: Inspection & Maintenance (`koelinstallaties-inspectie-en-onderhoud_theorie_168`)

### 🔥 PRIORITY 1 - Useful for Agent

#### 9. Pressure Switch Adjustment Diagram
**Chunk ID**: `ecf2283b-cd3c-4ba2-bdbb-8e4651285de8`
**Page**: 44 (page-045)
**Type**: Diagram with scales
**Description**: LP/HP pressostat adjustment (Start/Stop/Diff)

**Agent Value**: ⭐⭐⭐⭐ HIGH
- Relevant for "3 P's - Procesinstellingen"
- Shows settings ranges
- LP: CUT IN, DIFF scales
- HP: CUT OUT, DIFF scales

**Mermaid Advantages**:
- Can represent as decision tables
- Show threshold values
- Useful for settings verification

**Status**: ⏳ NEEDS CREATION

---

### ⚪ PRIORITY 2-3 - Keep as Images

Most inspection manual visuals are photos or equipment labels:
- `c82b4f97-c577-49e4-aef2-3029d43a0330` - Frozen evaporator inspection (keep as photo)
- Safety signs (all keep as images)
- Measurement equipment photos (all keep as images)
- `c7ebc758-c163-45fc-ab00-65b8a46a4736` - P-h diagram for R507 (keep as image)

---

## Summary: Diagrams to Create in Mermaid

### ✅ Already Created (Phase 1)
1. **SMIDO Main Flowchart** (`smido_main_flowchart.mermaid`)
2. **SMIDO 3 P's Breakdown** (`smido_3ps_diagnosis.mermaid`)
3. **Frozen Evaporator Example** (`smido_frozen_evaporator_example.mermaid`)
4. **Data Integration** (`smido_data_integration.mermaid`)

### 🔨 To Create (Phase 2)

#### High Priority (Create Now)
1. **Balance Diagram** - Component vs. factors equilibrium
   - Source: `chunk-4806fb93` (page-012, storingzoeken manual)
   - Type: Bidirectional relationship graph

2. **Troubleshooting Table Flow** - Symptom → Cause → Solution
   - Source: `chunk-9e024d44` (page-023, storingzoeken manual)
   - Type: Linear flowchart

3. **Basic Refrigeration Cycle** - 4-component simple cycle
   - Source: `chunk-e91e4028` (page-009, opbouw-en-werking manual)
   - Type: Circular flow diagram

4. **Schematic with Instrumentation** - System with P/T sensors
   - Source: `chunk-6c631446` (page-009, opbouw-en-werking manual)
   - Type: Annotated cycle diagram

5. **Pressostat Adjustment Logic** - LP/HP settings
   - Source: `chunk-ecf2283b` (page-045, inspectie-en-onderhoud manual)
   - Type: Decision table / threshold diagram

#### Medium Priority (Phase 3)
6. **Multi-Evaporator System** - Different temperature zones
   - Source: `chunk-2d32a8ed` (page-137, opbouw-en-werking manual)
   - Type: System architecture diagram

7. **Hot Gas Defrost System** - Defrost valve sequencing
   - Source: `chunk-424a4dc3` (page-114, opbouw-en-werking manual)
   - Type: Valve state diagram

---

## Metadata Structure for Diagrams

Each Mermaid diagram should include:

```yaml
---
# Diagram Metadata
title: "Diagram Title"
source_manual: "Manual filename"
source_chunk_id: "UUID from JSONL"
source_page: "Page number"
original_asset: "Path to original PNG"
diagram_type: "flowchart|graph|stateDiagram|etc"
smido_relevance: "Which SMIDO step(s) this supports"
failure_modes: ["List of relevant failure modes"]
components: ["List of components shown"]
created_date: "2024-11-11"
agent_usage: "How agent should use this diagram"
---
```

---

## Agent Usage Matrix

| Diagram | SMIDO Phase | Agent Use Case | Priority |
|---------|-------------|----------------|----------|
| SMIDO Flowchart | All | Main decision tree logic | ⭐⭐⭐⭐⭐ |
| Balance Diagram | D (Diagnose) | System imbalance detection | ⭐⭐⭐⭐ |
| Troubleshooting Table | M→O | Symptom-to-solution mapping | ⭐⭐⭐⭐ |
| Basic Cycle | I (Installatie) | System familiarity | ⭐⭐⭐⭐⭐ |
| Schematic with P/T | D (3 P's) | Measurement point identification | ⭐⭐⭐⭐ |
| Pressostat Settings | D (Procesinstellingen) | Settings verification | ⭐⭐⭐⭐ |
| Multi-Evaporator | I+D | Complex system understanding | ⭐⭐⭐ |
| Hot Gas Defrost | O (Onderdelen) | Defrost troubleshooting | ⭐⭐⭐ |

---

## Next Steps

1. ✅ Phase 1 Complete - SMIDO diagrams created
2. ⏳ Phase 2 - Create high-priority diagrams (1-5 above)
3. ⏳ Phase 3 - Create medium-priority diagrams (6-7 above)
4. ⏳ Phase 4 - Add metadata headers to all diagrams
5. ⏳ Phase 5 - Create master catalog with usage guidance

---

## File Organization

```
docs/diagrams/
├── smido/                          # SMIDO methodology (✅ Complete)
│   ├── smido_main_flowchart.mermaid
│   ├── smido_3ps_diagnosis.mermaid
│   ├── smido_frozen_evaporator_example.mermaid
│   └── smido_data_integration.mermaid
├── system/                         # System fundamentals (⏳ To create)
│   ├── basic_refrigeration_cycle.mermaid
│   ├── schematic_with_instrumentation.mermaid
│   ├── balance_diagram.mermaid
│   └── multi_evaporator_system.mermaid
├── troubleshooting/                # Diagnostic aids (⏳ To create)
│   ├── troubleshooting_table_flow.mermaid
│   ├── pressostat_adjustment_logic.mermaid
│   └── hot_gas_defrost_system.mermaid
└── DIAGRAM_CATALOG.md             # Master index
```

---

## Conversion Notes

### Flowcharts → Mermaid
- Diamond shapes = decision points `{condition?}`
- Rectangles = actions `[action]`
- Rounded rectangles = start/end `([label])`
- Arrows with labels = conditions `-->|Yes|`

### System Diagrams → Mermaid
- Components = nodes with icons/labels
- Connections = edges with flow direction
- Annotations = subgraphs or notes
- States = different node styles

### Tables → Mermaid
- Use flowchart with columns
- Or use actual table syntax (limited)
- Or create decision tree from table logic

---

## Traceability Template

Each diagram file will include header comment:

```mermaid
%% ============================================================
%% Diagram: [Diagram Name]
%% Source: [Manual filename]
%% Chunk: [chunk_id]
%% Page: [page number]
%% Asset: [path to original PNG]
%% SMIDO: [relevant phase(s)]
%% Usage: [agent use case]
%% Created: 2024-11-11
%% ============================================================
```

---

## Total Count

- **Visuals in storingzoeken manual**: 10 figures
  - **Convert to Mermaid**: 3 (SMIDO flowchart ✅, Balance ⏳, Troubleshooting table ⏳)
  - **Keep as images**: 7 (photos, P-h diagram, train, mobile unit)

- **Visuals in opbouw-en-werking manual**: 179 figures
  - **Convert to Mermaid**: 3-4 (Basic cycle, Schematic, Multi-evap, Defrost)
  - **Keep as images**: 175+ (photos, complex P&IDs, P-h diagrams, equipment)

- **Visuals in inspectie-en-onderhoud manual**: 43 figures
  - **Convert to Mermaid**: 1 (Pressostat adjustment)
  - **Keep as images**: 42 (photos, safety signs, equipment, tools)

**Total Mermaid Diagrams**: 4 complete + 7 to create = **11 total**

---

## Agent Integration Strategy

### How Agent Will Use Mermaid Diagrams

1. **At Runtime**: Parse Mermaid to build decision tree
2. **In Responses**: Reference diagram nodes in explanations
3. **For Navigation**: Use flowchart structure to guide user
4. **For Validation**: Check if measured values match diagram states
5. **For Learning**: Train on diagram structure as knowledge graph

### Storage Strategy

- **Mermaid files**: Version control, easy to edit
- **PNG renders**: For documentation/UI display
- **SVG exports**: For scalable web display
- **Metadata YAML**: For semantic search in Weaviate

---

## Quality Checklist

For each Mermaid diagram:
- [ ] Accurate translation from original
- [ ] Metadata header complete
- [ ] Node labels in Dutch (matching manual)
- [ ] English annotations in comments
- [ ] Color coding consistent
- [ ] Validates in Mermaid Live Editor
- [ ] Links back to source chunk
- [ ] Agent usage documented

