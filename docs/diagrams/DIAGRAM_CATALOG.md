# VSM Mermaid Diagrams - Master Catalog

**Complete index of all Mermaid diagrams with metadata and agent usage guidance**

**Last Updated**: November 11, 2024  
**Total Diagrams**: 11  
**Status**: 7 created, 4 planned

---

## Quick Reference

| # | Diagram Name | Type | Priority | Status | SMIDO Phase | Agent Usage |
|---|--------------|------|----------|--------|-------------|-------------|
| 1 | SMIDO Main Flowchart | Flowchart | ⭐⭐⭐⭐⭐ | ✅ | All | Decision tree logic |
| 2 | SMIDO 3 P's Diagnosis | Flowchart | ⭐⭐⭐⭐⭐ | ✅ | D | Diagnose phase detail |
| 3 | Frozen Evaporator Example | Flowchart | ⭐⭐⭐⭐ | ✅ | All | Demo scenario |
| 4 | Data Integration | Architecture | ⭐⭐⭐ | ✅ | - | System architecture |
| 5 | Balance Diagram | Graph | ⭐⭐⭐⭐ | ✅ | D | System equilibrium |
| 6 | Troubleshooting Table Flow | Flowchart | ⭐⭐⭐⭐ | ✅ | All | Response template |
| 7 | Basic Refrigeration Cycle | Cycle | ⭐⭐⭐⭐⭐ | ✅ | I | System familiarity |
| 8 | Schematic with Instrumentation | Annotated | ⭐⭐⭐⭐ | ✅ | D (P3) | Measurement points |
| 9 | Pressostat Adjustment Logic | Decision | ⭐⭐⭐⭐ | ✅ | D (P2) | Settings verification |
| 10 | Multi-Evaporator System | System | ⭐⭐⭐ | ⏳ | I+D | Complex systems |
| 11 | Hot Gas Defrost System | System | ⭐⭐⭐ | ⏳ | O | Defrost troubleshooting |

---

## Detailed Catalog

### SMIDO Methodology Diagrams

#### 1. SMIDO Main Flowchart ✅
**File**: `smido_main_flowchart.mermaid`  
**Type**: Flowchart (TD - Top Down)  
**Source**: N/A (synthesized from manual content)  
**SMIDO Phase**: All (M→T→I→D→O)  
**Priority**: ⭐⭐⭐⭐⭐ CRITICAL

**Metadata**:
- Chunk ID: N/A (conceptual diagram)
- Source Manual: storingzoeken-koeltechniek_theorie_179
- Related Chunk: `55a1e55e-41af-47d2-8f3e-6453dc49c84d` (original flowchart)
- Page Reference: Page 8 (Figuur 2)

**Content**:
- Complete M→T→I→D→O workflow
- All decision points with feedback loops
- 3 P's + Product Input breakdown
- Multiple resolution paths
- Escalation procedures

**Agent Usage**:
- **Primary use**: Main decision tree structure
- **Runtime**: Parse nodes to build conversation flow
- **Responses**: Reference current step in flowchart
- **Navigation**: Guide user through SMIDO phases
- **Validation**: Check if all steps were followed

**Related Diagrams**: #2 (3 P's detail), #3 (Example flow)

---

#### 2. SMIDO 3 P's Diagnosis Detail ✅
**File**: `smido_3ps_diagnosis.mermaid`  
**Type**: Flowchart (TD)  
**Source**: N/A (synthesized)  
**SMIDO Phase**: D (Diagnose)  
**Priority**: ⭐⭐⭐⭐⭐ CRITICAL

**Metadata**:
- Chunk ID: N/A (conceptual)
- Source Manual: storingzoeken-koeltechniek_theorie_179
- Page Reference: Pages 9-10

**Content**:
- P1: Power (voltage, fuses, current)
- P2: Procesinstellingen (thermostat, pressostat, timers, controller)
- P3: Procesparameters (pressures, temps, superheat, subcooling)
- P4: Productinput (load, ambient, airflow, door frequency)

**Agent Usage**:
- **Primary use**: Guide systematic diagnosis
- **Checklist**: Generate diagnostic questions
- **Tool calls**: Map to specific measurement tools
- **Reporting**: Structure diagnostic findings

**Related Diagrams**: #1 (Main flow), #8 (Instrumentation), #9 (Settings)

---

#### 3. Frozen Evaporator Example ✅
**File**: `smido_frozen_evaporator_example.mermaid`  
**Type**: Flowchart (TD)  
**Source**: Real-world scenario  
**SMIDO Phase**: All (complete M→T→I→D→O)  
**Priority**: ⭐⭐⭐⭐ HIGH

**Metadata**:
- Chunk ID: `d17a0b0b-6ed0-4e75-8094-36b64a2aa361` (frozen evap photo)
- Source Manual: storingzoeken-koeltechniek_theorie_179
- Page Reference: Page 7 (Figuur 1)
- Vlog Reference: A3 case
- Telemetry Flags: `_flag_main_temp_high`, `_flag_suction_extreme`

**Content**:
- Complete troubleshooting workflow for frozen evaporator
- Integration of manual + vlog + telemetry
- M: Symptoms (temp too high, ice formation)
- T: Visual inspection (thick ice layer)
- I: Review defrost cycle settings
- D: Measure suction line temperature (P3)
- O: Manual defrost, clean ducts, calibrate thermostat

**Agent Usage**:
- **Demo scenario**: Show complete SMIDO workflow
- **Training**: Example of data source integration
- **Templates**: Pattern for other failure modes
- **Validation**: Verify agent logic completeness

**Related Diagrams**: #1 (Main flow), #5 (Balance), #11 (Defrost)

---

#### 4. Data Integration Architecture ✅
**File**: `smido_data_integration.mermaid`  
**Type**: Architecture diagram (TD)  
**Source**: System design  
**SMIDO Phase**: N/A (meta-level)  
**Priority**: ⭐⭐⭐ MEDIUM

**Metadata**:
- Chunk ID: N/A (system architecture)
- Purpose: Show VSM data sources and flow

**Content**:
- Telemetry: 785K datapoints → WorldState features
- Manuals: 922 chunks → ~200 sections
- Vlogs: 15 clips → 5 cases
- Integration through Weaviate
- Agent tools and semantic search

**Agent Usage**:
- **Documentation**: System overview
- **Development**: Architecture reference
- **Onboarding**: Understanding VSM design
- **Not runtime**: Conceptual, not for troubleshooting

**Related Diagrams**: None (standalone architecture)

---

### System Understanding Diagrams

#### 5. Balance Diagram ✅
**File**: `system/balance_diagram.mermaid`  
**Type**: Graph (bidirectional relationships)  
**Source**: storingzoeken-koeltechniek_theorie_179  
**SMIDO Phase**: D (Diagnose) - System balance understanding  
**Priority**: ⭐⭐⭐⭐ HIGH

**Metadata**:
- **Chunk ID**: `4806fb93-38a9-43bb-a3bf-33e32c837581`
- **Page**: 12 (page-012)
- **Figure**: Figuur 3 "In balans"
- **Manual**: storingzoeken-koeltechniek_theorie_179
- **Asset Path**: `features/extraction/production_output/storingzoeken-koeltechniek_theorie_179/storingzoeken-koeltechniek_theorie_179/assets/page-012/chunk-4806fb93-38a9-43bb-a3bf-33e32c837581.png`

**Content**:
- **Components** (Left): Expansieorgaan, Verdamper, Compressor, Condensor
- **Factors** (Right): Koudemiddel hoeveelheid, Koellast, Motorvermogen, Lucht/water, Omgevingstemperatuur
- **Relationships**: Bidirectional "Onderlinge relatie"
- **Balance States**: Ondergrens (too low), Bandbreedte (OK), Bovengrens (too high)

**Agent Usage**:
- **Diagnostic phase**: Explain "Koelproces uit balans" concept
- **Root cause**: Identify which factor is out of balance
- **Education**: Help technician understand system interactions
- **Tool selection**: Determine which measurements needed

**Example Agent Query**:
```
User: "Why is the evaporator freezing?"
Agent: [Uses balance diagram]
       "The cooling process is out of balance. Let me check:
        - Component side: Evaporator may be undersized OR
        - Factor side: Too much refrigerant, or airflow too low
        Based on your telemetry, I see low airflow (vervuilde luchtkanalen)"
```

**Related Diagrams**: #1 (SMIDO), #7 (Basic cycle)

---

#### 6. Troubleshooting Table Flow ✅
**File**: `troubleshooting/troubleshooting_table_flow.mermaid`  
**Type**: Linear flowchart (LR - Left to Right)  
**Source**: storingzoeken-koeltechniek_theorie_179  
**SMIDO Phase**: All - Response formatting template  
**Priority**: ⭐⭐⭐⭐ HIGH

**Metadata**:
- **Chunk ID**: `9e024d44-bc1b-4a36-b7a8-eec8614a838f`
- **Page**: 22 (page-023)
- **Figure**: Figuur 5 "Opbouw storingstabel"
- **Manual**: storingzoeken-koeltechniek_theorie_179
- **Asset Path**: `features/extraction/production_output/storingzoeken-koeltechniek_theorie_179/storingzoeken-koeltechniek_theorie_179/assets/page-023/chunk-9e024d44-bc1b-4a36-b7a8-eec8614a838f.png`

**Content**:
- **Step 1**: Verschijnselen (Symptoms) - Location in installation
- **Step 2**: Mogelijke oorzaken (Possible causes) - Numbered list
- **Step 3**: Oplossingen (Solutions) - What to check

**Agent Usage**:
- **Response template**: Format troubleshooting advice
- **Structured output**: Organize findings
- **User communication**: Clear symptom → cause → solution flow
- **Documentation**: Generate troubleshooting reports

**Example Agent Response Format**:
```
VERSCHIJNSELEN:
- Te hoge temperatuur in koelcel
- Compressor draait continu
- Locatie: Verdamper

MOGELIJKE OORZAKEN:
1. Vervuilde verdamper (verminderde warmteoverdracht)
2. Te weinig koudemiddel (lekkage)
3. Defecte ontdooitimer

OPLOSSINGEN:
✓ Controleer verdamper op ijsvorming
✓ Meet zuig- en persdruk
✓ Test ontdooitimer functie
```

**Related Diagrams**: #1 (SMIDO), #3 (Example)

---

#### 7. Basic Refrigeration Cycle ✅
**File**: `system/basic_refrigeration_cycle.mermaid`  
**Type**: Circular graph (TD)  
**Source**: koelinstallaties-opbouw-en-werking_theorie_2016  
**SMIDO Phase**: I (Installatie Vertrouwd)  
**Priority**: ⭐⭐⭐⭐⭐ CRITICAL

**Metadata**:
- **Chunk ID**: `e91e4028-a83e-48a3-8798-ba7d216ad2cd`
- **Page**: 8 (page-009)
- **Figure**: Figuur 3 "De hoofdcomponenten in een koelkring"
- **Manual**: koelinstallaties-opbouw-en-werking_theorie_2016
- **Asset Path**: `features/extraction/production_output/koelinstallaties-opbouw-en-werking_theorie_2016/koelinstallaties-opbouw-en-werking_theorie_2016/assets/page-009/chunk-e91e4028-a83e-48a3-8798-ba7d216ad2cd.png`

**Content**:
- **4 Main Components**: Compressor → Condensor → Capillair → Verdamper
- **Pressure Zones**: Hoge druk (high) / Lage druk (low)
- **State Changes**: Gas → Liquid → Two-phase → Gas
- **Functions**: Drukverhogend, Warmteafvoer, Drukverlaging, Warmteopname

**Agent Usage**:
- **Education**: Teach basic cooling cycle
- **Familiarity check** (I phase): Verify technician understands system
- **Component identification**: Name parts and their functions
- **Flow explanation**: Describe refrigerant path
- **Foundation**: Basis for more complex diagrams

**Example Agent Interaction**:
```
Agent: "Before we diagnose, let me confirm you understand the system.
        [Shows basic cycle diagram]
        Can you identify the 4 main components?
        Where would you measure the suction pressure?"
User: "At the verdamper outlet?"
Agent: "Correct! That's in the lage druk zone, between verdamper and compressor."
```

**Related Diagrams**: #8 (Instrumentation), #5 (Balance)

---

#### 8. Schematic with Instrumentation ✅
**File**: `system/schematic_with_instrumentation.mermaid`  
**Type**: Annotated flowchart (TD)  
**Source**: koelinstallaties-opbouw-en-werking_theorie_2016  
**SMIDO Phase**: D (Diagnose - P3: Procesparameters)  
**Priority**: ⭐⭐⭐⭐ HIGH

**Metadata**:
- **Chunk ID**: `6c631446-7f65-475e-8df0-8109a44e85f9`
- **Page**: 8 (page-009)
- **Figure**: Figuur 4 "Schematisch weergave koelinstallatie"
- **Manual**: koelinstallaties-opbouw-en-werking_theorie_2016
- **Asset Path**: `features/extraction/production_output/koelinstallaties-opbouw-en-werking_theorie_2016/koelinstallaties-opbouw-en-werking_theorie_2016/assets/page-009/chunk-6c631446-7f65-475e-8df0-8109a44e85f9.png`

**Content**:
- Complete cooling cycle with measurement points
- **P sensors** (Pressure): 4 locations marked
- **T sensors** (Temperature): 2 locations marked
- **Heat flows**: Warmtetoevoer (in), Warmteafvoer (out)
- **Zones**: High/low pressure clearly labeled

**Agent Usage**:
- **Measurement guidance**: Tell technician WHERE to measure
- **Expected values**: Compare telemetry with diagram annotations
- **P3 Procesparameters**: Guide through pressure/temp measurements
- **Sensor validation**: Verify all sensors functioning
- **Diagnostic tool**: Map telemetry data to physical locations

**Example Agent Interaction**:
```
Agent: "Let's check your procesparameters (3 P's - P3).
        [Shows instrumentation diagram]
        Measure these 4 pressure points:
        📊 P (hoog): After compressor - expect ~9 bar
        📊 P (hoog): After condensor - expect ~9 bar  
        📊 P (laag): After expansion - expect ~1.4 bar
        📊 P (laag): After verdamper - expect ~1.4 bar
        
        Your telemetry shows P(laag) = 0.8 bar ⚠️
        This is too low - possible refrigerant leak!"
```

**Related Diagrams**: #7 (Basic cycle), #2 (3 P's), #9 (Pressostat)

---

#### 9. Pressostat Adjustment Logic ✅
**File**: `troubleshooting/pressostat_adjustment_logic.mermaid`  
**Type**: Decision diagram (TD)  
**Source**: koelinstallaties-inspectie-en-onderhoud_theorie_168  
**SMIDO Phase**: D (Diagnose - P2: Procesinstellingen)  
**Priority**: ⭐⭐⭐⭐ HIGH

**Metadata**:
- **Chunk ID**: `ecf2283b-cd3c-4ba2-bdbb-8e4651285de8`
- **Page**: 44 (page-045)
- **Figure**: Figuur 22 "Afstellen pressostaten"
- **Manual**: koelinstallaties-inspectie-en-onderhoud_theorie_168
- **Asset Path**: `features/extraction/production_output/koelinstallaties-inspectie-en-onderhoud_theorie_168/koelinstallaties-inspectie-en-onderhoud_theorie_168/assets/page-045/chunk-ecf2283b-cd3c-4ba2-bdbb-8e4651285de8.png`

**Content**:
- **LP Pressostaat**: START (CUT IN), DIFF, STOP logic
  - Range: 0.7 - 7.5 bar (10 - 107 psi)
  - Diff: 0.35 - 7.5 bar (5 - 107 psi)
- **HP Pressostaat**: STOP (CUT OUT), DIFF, START logic
  - Range: 7 - 28 bar (100 - 437 psi)
  - Diff: 6 - 14 bar (30 - 80 psi)

**Agent Usage**:
- **Settings verification** (P2): Check if pressostat settings correct
- **Troubleshooting**: Diagnose compressor cycling issues
- **Adjustment guide**: Help technician adjust settings
- **Safety**: Verify HP cutout prevents over-pressure

**Example Agent Interaction**:
```
Agent: "Your compressor is short-cycling. Let's check procesinstellingen (P2).
        [Shows pressostat logic]
        
        LP Pressostaat should be:
        START: 2.0 bar (when pressure rises to this, compressor ON)
        DIFF: 1.0 bar (pressure must drop 1.0 bar to turn OFF)
        So STOP = 2.0 - 1.0 = 1.0 bar
        
        Your current settings: START=3.5, DIFF=0.5
        This causes compressor to cycle between 3.5 and 3.0 bar - too narrow!
        
        Recommended: START=2.0, DIFF=1.5 (cycle: 2.0 ↔ 0.5 bar)"
```

**Related Diagrams**: #2 (3 P's), #8 (Instrumentation)

---

### System Diagrams

#### 5. Balance Diagram ✅
[See detailed entry above]

#### 6. Troubleshooting Table Flow ✅
[See detailed entry above]

#### 7. Basic Refrigeration Cycle ✅
[See detailed entry above]

#### 8. Schematic with Instrumentation ✅
[See detailed entry above]

---

### Planned Diagrams (Phase 3)

#### 10. Multi-Evaporator System ⏳
**File**: `system/multi_evaporator_system.mermaid` (to create)  
**Type**: System architecture (TD)  
**Source**: koelinstallaties-opbouw-en-werking_theorie_2016  
**SMIDO Phase**: I+D  
**Priority**: ⭐⭐⭐ MEDIUM

**Metadata**:
- **Chunk ID**: `2d32a8ed-630c-4e5f-968a-f2eba21ac5b6`
- **Page**: 136 (page-137)
- **Figure**: Figuur 116 "Schema meervoudig systeem met verschillende verdampertemperaturen"
- **Manual**: koelinstallaties-opbouw-en-werking_theorie_2016

**Content**:
- 3 evaporators at different temperatures (-10°C, -5°C, 0°C)
- Pressure controllers (PC) for each zone
- Temperature controllers (TC) for each evaporator
- Common liquid supply and suction lines

**Agent Usage**:
- **Complex systems**: Understand multi-zone installations
- **Pressure regulation**: Diagnose multiple evaporator issues
- **Advanced troubleshooting**: Handle commercial refrigeration

**Status**: ⏳ PLANNED (not yet created)

---

#### 11. Hot Gas Defrost System ⏳
**File**: `troubleshooting/hot_gas_defrost_system.mermaid` (to create)  
**Type**: System schematic with valve states (TD)  
**Source**: koelinstallaties-opbouw-en-werking_theorie_2016  
**SMIDO Phase**: O (Onderdelen) - Defrost troubleshooting  
**Priority**: ⭐⭐⭐ MEDIUM

**Metadata**:
- **Chunk ID**: `424a4dc3-637e-45f1-9b3b-3554ae466b42`
- **Page**: 113 (page-114)
- **Figure**: Figuur 1 "Schema van koelinstallatie met heetgasontdooiing"
- **Manual**: koelinstallaties-opbouw-en-werking_theorie_2016

**Content**:
- 3 evaporators (A, B, C) with hot gas defrost
- Valve sequencing (open/dicht legend)
- Hot gas bypass lines
- Defrost cycle logic

**Agent Usage**:
- **Frozen evaporator** (Case A3): Troubleshoot defrost issues
- **Valve states**: Verify valves open/close correctly
- **Defrost cycle**: Explain how hot gas defrost works
- **Component isolation** (O): Test individual evaporator defrost

**Example Agent Use**:
```
Agent: "Your evaporator is frozen. Let's check the defrost system.
        [Shows hot gas defrost diagram]
        During defrost, valves 4, 8, 12 should OPEN (hot gas in)
        And valves 1, 5, 9 should CLOSE (stop liquid feed)
        
        Test each valve:
        ✓ Valve 4 (Evaporator A defrost) - is it opening?
        ✓ Valve 1 (Evaporator A liquid) - is it closing?"
```

**Status**: ⏳ PLANNED (not yet created)

---

## Usage Patterns

### Pattern 1: Sequential Diagnosis
```
Agent flow:
1. Show SMIDO Main Flowchart (#1) - "Here's our approach"
2. Drill into 3 P's Diagnosis (#2) - "Let's check systematically"
3. Show Instrumentation Diagram (#8) - "Measure here"
4. Reference Pressostat Logic (#9) - "Check these settings"
5. Show Balance Diagram (#5) - "Here's what's out of balance"
```

### Pattern 2: Example-Based Learning
```
Agent flow:
1. Show Frozen Evaporator Example (#3) - "Here's a similar case"
2. Reference Basic Cycle (#7) - "This is how it normally works"
3. Show Defrost System (#11) - "This is what failed"
4. Use Troubleshooting Table (#6) - "Here's the structured solution"
```

### Pattern 3: Component Education
```
Agent flow:
1. Show Basic Cycle (#7) - "These are the 4 main components"
2. Show Instrumentation (#8) - "These are the measurement points"
3. Show Balance Diagram (#5) - "These factors affect each component"
4. Reference SMIDO (#1) - "Now let's troubleshoot systematically"
```

---

## File Manifest

### Created Diagrams
```
docs/diagrams/
├── smido_main_flowchart.mermaid (2.8KB) ✅
├── smido_3ps_diagnosis.mermaid (1.2KB) ✅
├── smido_frozen_evaporator_example.mermaid (2.1KB) ✅
├── smido_data_integration.mermaid (2.0KB) ✅
├── system/
│   ├── balance_diagram.mermaid (NEW) ✅
│   ├── basic_refrigeration_cycle.mermaid (NEW) ✅
│   └── schematic_with_instrumentation.mermaid (NEW) ✅
└── troubleshooting/
    ├── troubleshooting_table_flow.mermaid (NEW) ✅
    └── pressostat_adjustment_logic.mermaid (NEW) ✅
```

### Planned Diagrams
```
docs/diagrams/
├── system/
│   └── multi_evaporator_system.mermaid ⏳
└── troubleshooting/
    └── hot_gas_defrost_system.mermaid ⏳
```

---

## Metadata Index

### By Source Manual

**storingzoeken-koeltechniek_theorie_179** (Troubleshooting):
- SMIDO Main Flowchart (chunk: `55a1e55e`)
- Balance Diagram (chunk: `4806fb93`)
- Troubleshooting Table Flow (chunk: `9e024d44`)
- Frozen Evaporator Example (chunk: `d17a0b0b`)

**koelinstallaties-opbouw-en-werking_theorie_2016** (Structure & Operation):
- Basic Refrigeration Cycle (chunk: `e91e4028`)
- Schematic with Instrumentation (chunk: `6c631446`)
- Multi-Evaporator System (chunk: `2d32a8ed`) ⏳
- Hot Gas Defrost System (chunk: `424a4dc3`) ⏳

**koelinstallaties-inspectie-en-onderhoud_theorie_168** (Inspection & Maintenance):
- Pressostat Adjustment Logic (chunk: `ecf2283b`)

### By SMIDO Phase

| SMIDO Phase | Diagrams |
|-------------|----------|
| **All phases** | #1 (Main flowchart), #3 (Example), #6 (Table flow) |
| **M** (Melding) | #6 (Table flow - symptoms) |
| **T** (Technisch) | #1 (Main flowchart) |
| **I** (Installatie) | #7 (Basic cycle), #10 (Multi-evap) ⏳ |
| **D** (Diagnose) | #2 (3 P's), #5 (Balance), #8 (Instrumentation), #9 (Pressostat) |
| **O** (Onderdelen) | #11 (Defrost system) ⏳ |

### By Failure Mode

| Failure Mode | Relevant Diagrams |
|--------------|-------------------|
| Te hoge temperatuur | #1, #3, #5, #6, #8 |
| Ingevroren verdamper | #3, #5, #7, #11 ⏳ |
| Compressor cycling | #1, #8, #9 |
| Pressure issues | #8, #9 |
| Settings incorrect | #2, #9 |
| System imbalance | #5, #7 |

---

## Agent Implementation Guide

### 1. At Startup
```python
# Load all Mermaid diagrams into memory
diagrams = {
    "smido_main": load_mermaid("smido_main_flowchart.mermaid"),
    "balance": load_mermaid("system/balance_diagram.mermaid"),
    # ... etc
}

# Parse metadata from headers
for diagram in diagrams:
    metadata = parse_metadata_header(diagram)
    index_by_smido_phase(metadata)
    index_by_chunk_id(metadata)
```

### 2. During Conversation
```python
# Agent selects diagram based on context
if current_smido_phase == "Diagnose":
    if checking_settings:
        show_diagram("pressostat_adjustment_logic")
    elif checking_measurements:
        show_diagram("schematic_with_instrumentation")
    elif system_imbalance:
        show_diagram("balance_diagram")
```

### 3. In Weaviate
```python
# Store diagram metadata in VSM_ManualSections
{
    "section_id": "diagram_balance",
    "title": "Koelproces in Balans",
    "content_type": "diagram",
    "smido_step": "diagnose",
    "diagram_path": "docs/diagrams/system/balance_diagram.mermaid",
    "source_chunk_id": "4806fb93-38a9-43bb-a3bf-33e32c837581",
    "failure_modes": ["koelproces_uit_balans", "te_hoge_temperatuur"],
    "components": ["expansieorgaan", "verdamper", "compressor", "condensor"]
}
```

---

## Conversion Quality Standards

### Each Mermaid Diagram Must:
1. ✅ Include complete metadata header (11 fields)
2. ✅ Use Dutch labels (matching manual language)
3. ✅ Include English annotations in comments
4. ✅ Link back to source chunk ID
5. ✅ Specify SMIDO relevance
6. ✅ Document agent usage
7. ✅ Use consistent color coding
8. ✅ Validate in Mermaid Live Editor
9. ✅ Include creation date
10. ✅ Provide example agent interactions

### Color Coding Standard
- 🔵 Blue (`#e1f5ff`) = M - Melding / Inputs
- 🟡 Yellow (`#fff9c4`) = T - Technisch / Quick checks
- 🟣 Purple (`#f3e5f5`) = I - Installatie / Familiarity
- 🟢 Green (`#e8f5e9`) = D - Diagnose / Analysis
- 🟠 Orange (`#ffe0b2`) = O - Onderdelen / Components
- 🔴 Red (`#ffcdd2`) = Problems / Failures
- 🟦 Indigo (`#c5cae9`) = Resolution / Success
- 🟩 Teal (`#e0f2f1`) = Data / Tools

---

## Export & Distribution

### For Documentation (mkdocs)
```bash
# All diagrams auto-render in markdown
# Include in docs/data/manuals_structure.md
```

### For Agent Runtime
```bash
# Parse Mermaid → NetworkX graph
# Extract nodes, edges, decisions
# Build decision tree programmatically
```

### For UI Display
```bash
# Export to PNG/SVG for dashboard
mmdc -i diagram.mermaid -o diagram.png
```

### For Weaviate Import
```bash
# Extract metadata → JSON
# Store diagram paths in VSM_ManualSections
# Enable semantic search on diagrams
```

---

## Maintenance

### Adding New Diagrams
1. Identify source chunk ID from `.visual_chunks.jsonl`
2. Create Mermaid file with metadata header
3. Test rendering in Mermaid Live Editor
4. Add entry to this catalog
5. Update file manifest
6. Document agent usage
7. Add to relevant SMIDO phase index

### Updating Existing Diagrams
1. Preserve chunk ID and source references
2. Increment version in comments
3. Update "Last Modified" date
4. Test rendering after changes
5. Update catalog if usage changes

---

## Statistics

- **Total diagrams**: 11 (9 created ✅, 2 planned ⏳)
- **Total size**: ~15KB (text-based, highly efficient)
- **Source chunks analyzed**: 233 visual chunks across 3 manuals
- **Conversion rate**: 11/233 = 4.7% (highly selective)
- **Agent-critical diagrams**: 5 (SMIDO, Balance, Cycle, Instrumentation, Table)
- **Coverage**: All 5 SMIDO phases represented

---

## References

- **Manual Analysis**: `docs/data/manuals_structure.md`
- **Diagram Guide**: `docs/diagrams/README.md`
- **SMIDO Methodology**: `docs/diagrams/smido_methodology.md`
- **Project Overview**: `CLAUDE.md`
- **Visual Chunks**: `features/extraction/production_output/*/visual_chunks.jsonl`

---

**Status**: ✅ Phase 2 Complete - 9 diagrams created with full metadata
**Next**: Phase 3 - Create multi-evaporator and defrost diagrams (optional)

