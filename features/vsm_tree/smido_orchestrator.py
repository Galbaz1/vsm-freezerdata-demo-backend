"""
SMIDO Orchestrator - Coordinates SMIDO workflow progression.

Manages phase transitions: M → T → I → D → O
Handles phase skipping and P-branch selection.
"""

from typing import Dict, Any, Optional, List
from elysia.tree.tree import Tree
from features.vsm_tree.context_manager import ContextManager


class SMIDOOrchestrator:
    """
    Coordinates SMIDO workflow: M → T → I → D → O
    Manages phase transitions based on tool results and user input.
    """
    
    def __init__(self, tree: Tree, context_manager: ContextManager):
        self.tree = tree
        self.context = context_manager
        self.phase_sequence: List[str] = ["melding", "technisch", "installatie", "diagnose", "onderdelen"]
        self.current_phase_index: int = 0
        self.completed_phases: List[str] = []
        self.skipped_phases: List[str] = []
    
    def get_current_phase(self) -> str:
        """Get current SMIDO phase"""
        if self.current_phase_index < len(self.phase_sequence):
            return self.phase_sequence[self.current_phase_index]
        return self.phase_sequence[-1]  # Return last phase if beyond
    
    def can_skip_phase(self, phase: str) -> bool:
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
        
        elif phase == "diagnose":
            # Skip if issue was resolved in previous phases
            return self.context.user_input.get("issue_resolved", False)
        
        return False
    
    def transition_to_next_phase(self, reason: Optional[str] = None) -> Optional[str]:
        """
        Move to next SMIDO phase.
        
        Args:
            reason: Optional reason for transition
        
        Returns:
            New phase name or None if at end
        """
        current_phase = self.get_current_phase()
        self.completed_phases.append(current_phase)
        
        if self.current_phase_index < len(self.phase_sequence) - 1:
            self.current_phase_index += 1
            new_phase = self.get_current_phase()
            self.context.set_smido_phase(new_phase)
            
            # Check if we should skip this phase
            if self.can_skip_phase(new_phase):
                self.skipped_phases.append(new_phase)
                # Auto-transition to next phase
                return self.transition_to_next_phase(f"Skipped {new_phase} based on context")
            
            return new_phase
        return None
    
    def should_branch_to_p(self, symptoms: Optional[Dict[str, Any]] = None) -> str:
        """
        Determine which P to start with based on symptoms or WorldState.
        Returns: "p1_power", "p2_procesinstellingen", "p3_procesparameters", "p4_productinput"
        
        Args:
            symptoms: Optional symptoms dict. If None, uses context.worldstate
        """
        if symptoms is None:
            symptoms = {}
            # Extract symptoms from worldstate
            flags = self.context.worldstate.get("flags", {})
            current_state = self.context.worldstate.get("current_state", {})
            
            # Check compressor status
            hot_gas = current_state.get("current_hot_gas_temp", 0)
            symptoms["compressor_not_running"] = hot_gas < 30
            
            # Check temperature
            room_temp = current_state.get("current_room_temp")
            target_temp = self.context.context.get("design_parameters", {}).get("target_temp", -33)
            if room_temp is not None:
                symptoms["temp_out_of_range"] = abs(room_temp - target_temp) > 5
                symptoms["system_running"] = hot_gas > 30
            
            # Check pressures (via flags)
            symptoms["abnormal_pressures"] = flags.get("suction_extreme", False) or flags.get("liquid_extreme", False)
            
            # Check external conditions
            ambient = current_state.get("current_ambient_temp", 0)
            symptoms["high_ambient"] = ambient > 30
            door_open_ratio = self.context.worldstate.get("trends_30m", {}).get("door_open_ratio_30m", 0)
            symptoms["excessive_door"] = door_open_ratio > 0.2
        
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
            if phase in self.completed_phases:
                status = "✅"
            elif phase in self.skipped_phases:
                status = "⏭️"
            elif i == self.current_phase_index:
                status = "⏳"
            else:
                status = "⏸️"
            
            phase_name = phase.upper()
            if phase == "melding":
                phase_name = "M - MELDING"
            elif phase == "technisch":
                phase_name = "T - TECHNISCH"
            elif phase == "installatie":
                phase_name = "I - INSTALLATIE VERTROUWD"
            elif phase == "diagnose":
                phase_name = "D - DIAGNOSE (4 P's)"
            elif phase == "onderdelen":
                phase_name = "O - ONDERDELEN UITSLUITEN"
            
            summary += f"{status} {phase_name}\n"
        
        if self.completed_phases:
            summary += f"\nCompleted: {', '.join(self.completed_phases)}\n"
        if self.skipped_phases:
            summary += f"Skipped: {', '.join(self.skipped_phases)}\n"
        summary += f"Current: {self.get_current_phase()}\n"
        
        return summary
    
    def reset(self):
        """Reset orchestrator to initial state"""
        self.current_phase_index = 0
        self.completed_phases = []
        self.skipped_phases = []
        self.context.set_smido_phase("melding")

