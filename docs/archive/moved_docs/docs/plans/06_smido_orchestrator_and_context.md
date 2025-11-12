# Plan 6: SMIDO Orchestrator + Context Manager

**Priority**: MEDIUM (Integrates everything together)  
**Parallelization**: Can start in parallel, but needs tools + nodes to complete  
**Estimated Time**: 4 hours

---

## Objective

Implement the SMIDO Orchestrator that coordinates workflow progression (M→T→I→D→O) and the Context Manager that maintains WorldState (W) and Context (C) throughout the troubleshooting session.

---

## Context Files Required

**Architecture**:
- `docs/diagrams/VSM_AGENT_ARCHITECTURE_MOTIVATION.md`:
  - Lines 68-80: SMIDO Orchestrator design
  - Lines 81-101: Context Manager design (W vs C split)
- `docs/diagrams/vsm_agent_architecture.mermaid` (orchestrator, context manager flow)

**SMIDO Workflow**:
- `docs/diagrams/smido_main_flowchart.mermaid` (complete workflow with decision points)
- `CLAUDE.md` (lines 247-263 - SMIDO methodology steps)

**WorldState/Context Definition**:
- `docs/data/SYNTHETIC_DATA_STRATEGY.md` (lines 264-296 - W vs C usage in tools)
- `CLAUDE.md` (lines 362-379 - W vs C split)

**Elysia Integration**:
- `elysia/tree/tree.py` (Tree class, how to manage tree execution)
- `elysia/tree/objects.py` (Environment, TreeData)
- `docs/diagrams/elysia/05_tree_lifecycle.mermaid` (tree execution flow)

---

## Implementation Tasks

### Task 6.1: Implement Context Manager

**File**: `features/vsm_tree/context_manager.py`

**Purpose**: Manage WorldState (W) and Context (C) throughout troubleshooting

**Implementation Spec**:

```python
from typing import Dict, Any
from datetime import datetime

class ContextManager:
    """
    Manages WorldState (W) and Context (C) for VSM troubleshooting.
    
    W (WorldState) - Dynamic:
    - Current sensor readings
    - Technician observations
    - Customer symptoms
    - Urgency assessment
    
    C (Context) - Static:
    - Installation design parameters
    - Commissioning data
    - Schemas
    - Service history
    """
    
    def __init__(self):
        self.worldstate = {}  # W
        self.context = {}  # C
        self.user_input = {}  # Technician observations
        self.smido_phase = "melding"
    
    def update_worldstate(self, worldstate: Dict):
        """Update dynamic WorldState (W) from ComputeWorldState tool"""
        self.worldstate.update(worldstate)
        self.worldstate["last_updated"] = datetime.now().isoformat()
    
    def load_context(self, asset_id: str, commissioning_data: Dict):
        """Load static Context (C) from FD_Assets"""
        self.context = {
            "asset_id": asset_id,
            "commissioning_data": commissioning_data,
            "design_parameters": commissioning_data.get("commissioning_data", {}),
            "components": commissioning_data.get("components", {}),
            "control_settings": commissioning_data.get("control_settings", {}),
            "balance_check_parameters": commissioning_data.get("balance_check_parameters", {})
        }
    
    def add_user_observation(self, observation_type: str, value: Any):
        """Add technician observation to WorldState"""
        if "observations" not in self.worldstate:
            self.worldstate["observations"] = []
        self.worldstate["observations"].append({
            "type": observation_type,
            "value": value,
            "timestamp": datetime.now().isoformat()
        })
    
    def set_smido_phase(self, phase: str):
        """Update current SMIDO phase"""
        self.smido_phase = phase
    
    def get_context_for_llm(self) -> str:
        """Format W+C for LLM prompts"""
        prompt = "## Current Situation (WorldState - W)\n"
        if "current_state" in self.worldstate:
            cs = self.worldstate["current_state"]
            prompt += f"- Room temp: {cs.get('room_temp', '?')}°C\n"
            prompt += f"- Hot gas: {cs.get('hot_gas_temp', '?')}°C\n"
            # ... more
        
        prompt += "\n## Installation Design (Context - C)\n"
        if "design_parameters" in self.context:
            dp = self.context["design_parameters"]
            prompt += f"- Target temp: {dp.get('target_temp', '?')}°C\n"
            prompt += f"- Design superheat: {dp.get('superheat_design', '?')}K\n"
            # ... more
        
        return prompt
    
    def to_tree_data_environment(self) -> Dict:
        """Export to TreeData.environment format"""
        return {
            "worldstate": self.worldstate,
            "context": self.context,
            "user_input": self.user_input,
            "smido_phase": self.smido_phase
        }
```

---

### Task 6.2: Implement SMIDO Orchestrator

**File**: `features/vsm_tree/smido_orchestrator.py`

**Purpose**: Coordinate SMIDO workflow progression

**Implementation Spec**:

```python
from typing import Dict, Any
from elysia.tree.tree import Tree

class SMIDOOrchestrator:
    """
    Coordinates SMIDO workflow: M → T → I → D → O
    Manages phase transitions based on tool results and user input.
    """
    
    def __init__(self, tree: Tree, context_manager: ContextManager):
        self.tree = tree
        self.context = context_manager
        self.phase_sequence = ["melding", "technisch", "installatie", "diagnose", "onderdelen"]
        self.current_phase_index = 0
    
    def get_current_phase(self) -> str:
        """Get current SMIDO phase"""
        return self.phase_sequence[self.current_phase_index]
    
    def can_skip_phase(self, phase: str, tree_data: Any) -> bool:
        """
        Determine if phase can be skipped based on context.
        
        Examples:
        - Skip T (Technisch) if obvious defect found
        - Skip I (Installatie) if technician is familiar
        - Skip D (Diagnose) if issue identified in T
        """
        if phase == "technisch":
            # Skip if obvious defect reported
            obs = self.context.worldstate.get("observations", [])
            return any(o.get("type") == "obvious_defect" for o in obs)
        
        elif phase == "installatie":
            # Skip if technician confirms familiarity
            return self.context.user_input.get("system_familiar", False)
        
        return False
    
    def transition_to_next_phase(self, reason: str = None):
        """Move to next SMIDO phase"""
        if self.current_phase_index < len(self.phase_sequence) - 1:
            self.current_phase_index += 1
            new_phase = self.get_current_phase()
            self.context.set_smido_phase(new_phase)
            
            # Activate corresponding branch in tree
            branch_id = f"smido_{new_phase}"
            # tree.set_active_branch(branch_id)  # If Elysia supports this
            
            return new_phase
        return None
    
    def should_branch_to_p(self, symptoms: Dict) -> str:
        """
        Determine which P to start with based on symptoms.
        Returns: "p1_power", "p2_procesinstellingen", "p3_procesparameters", "p4_productinput"
        """
        # If compressor not running → P1 (Power)
        if symptoms.get("compressor_not_running"):
            return "p1_power"
        
        # If temp out of range but system running → P2 (Settings)
        if symptoms.get("temp_out_of_range") and symptoms.get("system_running"):
            return "p2_procesinstellingen"
        
        # If pressures abnormal → P3 (Measurements)
        if symptoms.get("abnormal_pressures"):
            return "p3_procesparameters"
        
        # If high ambient or excessive door usage → P4 (External)
        if symptoms.get("high_ambient") or symptoms.get("excessive_door"):
            return "p4_productinput"
        
        # Default: Start with P1
        return "p1_power"
    
    def generate_smido_summary(self) -> str:
        """Generate summary of SMIDO phases completed"""
        summary = "## SMIDO Workflow Summary\n\n"
        for i, phase in enumerate(self.phase_sequence):
            status = "✅" if i < self.current_phase_index else "⏳" if i == self.current_phase_index else "⏸️"
            summary += f"{status} {phase.upper()}\n"
        return summary
```

---

### Task 6.3: Integrate with Elysia Tree

**File**: `features/vsm_tree/vsm_tree.py`

**Purpose**: Create complete VSM tree with orchestrator + context manager

**Implementation**:

```python
from elysia import Tree
from features.vsm_tree.smido_orchestrator import SMIDOOrchestrator
from features.vsm_tree.context_manager import ContextManager
from features.vsm_tree.smido_nodes import create_m_node, create_t_node, create_i_node, create_d_node, create_o_node

def create_vsm_tree() -> tuple[Tree, SMIDOOrchestrator, ContextManager]:
    """
    Create complete VSM tree with SMIDO orchestrator and context manager.
    """
    # Create base tree
    tree = Tree()
    
    # Create managers
    context_manager = ContextManager()
    orchestrator = SMIDOOrchestrator(tree, context_manager)
    
    # Create all SMIDO nodes
    create_m_node(tree)
    create_t_node(tree)
    create_i_node(tree)
    create_d_node(tree)  # Includes P1, P2, P3, P4
    create_o_node(tree)
    
    # Set initial phase
    context_manager.set_smido_phase("melding")
    
    return tree, orchestrator, context_manager
```

---

## Verification

**Success Criteria**:
- [ ] Context Manager stores W and C separately
- [ ] Context Manager exports to TreeData.environment
- [ ] SMIDO Orchestrator tracks current phase
- [ ] Phase transitions work (M→T→I→D→O)
- [ ] Can skip phases based on context
- [ ] D node branches to correct P based on symptoms

**Test**:
```python
tree, orchestrator, context = create_vsm_tree()

# Test phase progression
assert orchestrator.get_current_phase() == "melding"
orchestrator.transition_to_next_phase()
assert orchestrator.get_current_phase() == "technisch"

# Test context management
context.update_worldstate({"current_state": {"room_temp": -28}})
context.load_context("135_1570", {"target_temp": -33})
env = context.to_tree_data_environment()
assert "worldstate" in env
assert "context" in env
```

---

## Dependencies

**Required Before**:
- ⏳ SMIDO nodes created (Plan 5)
- ⏳ Tools implemented (Plans 1-4)

**Blocks**:
- A3 scenario end-to-end testing

---

## Related Files

**To Create**:
- `features/vsm_tree/smido_orchestrator.py`
- `features/vsm_tree/context_manager.py`
- `features/vsm_tree/vsm_tree.py`
- `features/vsm_tree/tests/test_orchestrator.py`
- `features/vsm_tree/tests/test_context_manager.py`

**To Reference**:
- `elysia/tree/tree.py` (Tree API)
- `elysia/tree/objects.py` (TreeData, Environment)


