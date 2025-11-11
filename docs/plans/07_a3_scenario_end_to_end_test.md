# Plan 7: A3 Frozen Evaporator - End-to-End Test

**Priority**: HIGH (Integration test and demo validation)  
**Parallelization**: Depends on all previous plans  
**Estimated Time**: 2-3 hours

---

## Objective

Test complete SMIDO workflow with A3 "Ingevroren Verdamper" (Frozen Evaporator) scenario. Verify all data sources integrate correctly, tools execute properly, and agent provides correct diagnosis.

---

## Context Files Required

**Scenario Documentation**:
- `CLAUDE.md` (lines 372-387 - A3 scenario details)
- `docs/data/vlogs_processing_results.md` (lines 73-98 - A3 case description)
- `docs/diagrams/smido_frozen_evaporator_example.mermaid` (complete workflow)

**Expected Data Coverage**:
- VSM_VlogCase: A3 case
- VSM_TelemetryEvent: Frozen evaporator events
- VSM_ManualSections: Frozen evaporator sections
- VSM_WorldStateSnapshot: ws_frozen_evaporator_A3
- VSM_Diagram: smido_frozen_evaporator_example

**Architecture**:
- `docs/diagrams/VSM_AGENT_ARCHITECTURE_SUMMARY.md` (lines 86-100 - A3 data flow example)

---

## Test Scenario

### Initial State

**User Input**: "Koelcel bereikt temperatuur niet"

**Expected WorldState** (from telemetry):
- Room temp: 0°C (critical - should be -33°C)
- Flags: `_flag_main_temp_high=True`, `_flag_suction_extreme=True`
- Trend: Rising (2.8°C/hour)
- Door: Mostly closed

**Expected Diagnosis**: Frozen evaporator (ingevroren_verdamper)

---

## Test Flow

### Phase M - Melding

**Expected Actions**:
1. GetAlarms tool called → Finds active alarms
2. GetAssetHealth tool called → W vs C comparison shows temp too high
3. Questions asked: Urgency? Goods at risk? When did it start?

**Expected Output**:
- Symptom: Temperature too high (0°C vs -33°C target)
- Urgency: Critical (goods at risk)
- Duration: >2 hours

**Transition**: M → T

---

### Phase T - Technisch

**Expected Actions**:
1. Ask technician: Visual inspection?
2. GetAssetHealth for quick health check

**Expected User Input**: "Verdamper bedekt met dikke ijslaag"

**Expected Output**:
- Visual defect identified: Frozen evaporator
- But need to find root cause (not just symptom)

**Transition**: T → I (if not familiar) or T → D (if familiar)

---

### Phase I - Installatie

**Expected Actions**:
1. SearchManualsBySMIDO (smido_step="installatie_vertrouwd")
2. Show basic refrigeration cycle diagram
3. Ask: Familiar with defrost system?

**Expected Output**:
- Technician confirms understanding
- Schemas provided if needed

**Transition**: I → D

---

### Phase D - Diagnose (P3: Procesparameters)

**Expected Actions**:
1. ComputeWorldState → Full feature computation
2. AnalyzeSensorPattern → Matches ws_frozen_evaporator_A3 snapshot
3. SearchManualsBySMIDO (smido_step="procesparameters", failure_mode="ingevroren_verdamper")

**Expected Output**:
- Pattern match: Frozen evaporator
- Out of balance factors: Defrost cycle not working, poor airflow
- Manual section: "Koelproces uit balans" page 11-12

**Transition**: D → O (component isolation)

---

### Phase O - Onderdelen

**Expected Actions**:
1. QueryVlogCases (failure_mode="ingevroren_verdamper") → Finds A3 case
2. SearchManualsBySMIDO (smido_step="ketens_onderdelen") → Component isolation guide

**Expected Output**:
- Similar case: A3_1, A3_2, A3_3 (complete workflow)
- Root cause: Defrost timer defect + vervuilde luchtkanalen
- Solution steps:
  1. Manual defrost
  2. Clean air ducts
  3. Calibrate thermostat
  4. Test defrost cycle

**End**: Solution provided

---

## Implementation Tasks

### Task 7.1: Create Test Script

**File**: `features/vsm_tree/tests/test_a3_scenario.py`

**Implementation**:

```python
import pytest
from features.vsm_tree.vsm_tree import create_vsm_tree
from datetime import datetime

@pytest.mark.asyncio
async def test_a3_frozen_evaporator_complete_workflow():
    """
    Test complete SMIDO workflow for A3 frozen evaporator scenario.
    """
    # Setup
    tree, orchestrator, context = create_vsm_tree()
    
    # Initial query
    user_query = "Koelcel bereikt temperatuur niet"
    
    # M - Melding
    # Simulate tool calls
    # Verify alarms found
    # Verify urgency assessed
    
    # T - Technisch
    # Simulate visual inspection input
    # Verify frozen evaporator symptom recorded
    
    # I - Installatie
    # Verify schemas provided
    # Simulate technician familiarity confirmation
    
    # D - Diagnose (P3)
    # Verify WorldState computed
    # Verify pattern matched (ws_frozen_evaporator_A3)
    # Verify manual section retrieved
    
    # O - Onderdelen
    # Verify A3 vlog case found
    # Verify solution steps provided
    
    # Final verification
    assert orchestrator.get_current_phase() == "onderdelen"
    assert "ingevroren_verdamper" in context.worldstate.get("detected_failure_mode", "")
    assert len(context.worldstate.get("solution_steps", [])) >= 3
```

---

### Task 7.2: Create Interactive Demo Script

**File**: `scripts/demo_a3_scenario.py`

**Purpose**: Interactive demo showing SMIDO workflow with A3 scenario

**Implementation**:

```python
#!/usr/bin/env python3
"""
Interactive demo of A3 frozen evaporator scenario.
Shows complete SMIDO workflow with real data integration.
"""

import asyncio
from features.vsm_tree.vsm_tree import create_vsm_tree
from datetime import datetime

async def demo_a3_scenario():
    print("=" * 70)
    print("VSM DEMO: A3 Frozen Evaporator Scenario")
    print("=" * 70)
    
    # Initialize
    tree, orchestrator, context = create_vsm_tree()
    
    print("\n[USER] Koelcel bereikt temperatuur niet")
    
    # M - Melding
    print("\n--- M - MELDING ---")
    # Execute GetAlarms
    # Execute GetAssetHealth
    # Show results
    
    print("\n[AGENT] Symptomen gedetecteerd:")
    print("  - Temperatuur: 0°C (kritisch, moet -33°C zijn)")
    print("  - Alarm actief: Hoge temperatuur")
    print("  - Urgentie: Producten in gevaar")
    
    # Continue through T, I, D, O...
    # Show each phase's actions and outputs
    
    print("\n[AGENT] OPLOSSING:")
    print("  1. Handmatig ontdooien")
    print("  2. Luchtkanalen reinigen")
    print("  3. Thermostaat kalibreren")
    print("  4. Ontdooicyclus controleren")
    
    print("\n=" * 70)
    print("Demo complete!")

if __name__ == "__main__":
    asyncio.run(demo_a3_scenario())
```

---

## Verification

**Success Criteria**:
- [ ] Complete SMIDO workflow executes (M→T→I→D→O)
- [ ] All tools called in correct sequence
- [ ] A3 vlog case retrieved
- [ ] Frozen evaporator pattern detected
- [ ] Manual sections about defrost/balance retrieved
- [ ] Solution matches A3 vlog solution
- [ ] Execution time <30 seconds

**Expected Tool Call Sequence**:
1. GetAlarms → Active alarms
2. GetAssetHealth → W vs C shows temp too high
3. ComputeWorldState → Full feature computation
4. AnalyzeSensorPattern → Matches frozen evaporator pattern
5. SearchManualsBySMIDO → Defrost/balance sections
6. QueryVlogCases → A3 case with solution steps

---

## Dependencies

**Required Before**:
- ⏳ All tools implemented (Plans 1-4)
- ⏳ SMIDO nodes created (Plan 5)
- ⏳ SMIDO orchestrator implemented (Plan 6)

**Blocks**:
- Phase 5: Demo & Polish

---

## Related Files

**To Create**:
- `features/vsm_tree/tests/test_a3_scenario.py`
- `scripts/demo_a3_scenario.py`

**To Reference**:
- All VSM collections (for data verification)
- `docs/diagrams/smido_frozen_evaporator_example.mermaid` (expected flow)


