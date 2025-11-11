"""
Context Manager - Manages WorldState (W) and Context (C) for VSM troubleshooting.

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

from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import json


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
        self.worldstate: Dict[str, Any] = {}  # W
        self.context: Dict[str, Any] = {}  # C
        self.user_input: Dict[str, Any] = {}  # Technician observations
        self.smido_phase: str = "melding"
        self.asset_id: Optional[str] = None
    
    def update_worldstate(self, worldstate: Dict[str, Any]):
        """Update dynamic WorldState (W) from ComputeWorldState tool"""
        self.worldstate.update(worldstate)
        self.worldstate["last_updated"] = datetime.now().isoformat()
    
    def load_context(self, asset_id: str, commissioning_data: Optional[Dict[str, Any]] = None):
        """
        Load static Context (C) from FD_Assets or enrichment file.
        
        Args:
            asset_id: Asset identifier
            commissioning_data: Optional commissioning data dict. If None, loads from enrichment file.
        """
        self.asset_id = asset_id
        
        if commissioning_data is None:
            # Load from enrichment file
            enrichment_path = Path("features/integration_vsm/output/fd_assets_enrichment.json")
            if enrichment_path.exists():
                with open(enrichment_path) as f:
                    commissioning_data = json.load(f)
            else:
                raise FileNotFoundError(f"Enrichment file not found: {enrichment_path}")
        
        self.context = {
            "asset_id": asset_id,
            "commissioning_data": commissioning_data.get("commissioning_data", {}),
            "design_parameters": commissioning_data.get("commissioning_data", {}),
            "components": commissioning_data.get("components", {}),
            "control_settings": commissioning_data.get("control_settings", {}),
            "balance_check_parameters": commissioning_data.get("balance_check_parameters", {}),
            "operational_limits": commissioning_data.get("operational_limits", {})
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
    
    def add_user_input(self, key: str, value: Any):
        """Add user input (technician responses, symptoms, etc.)"""
        self.user_input[key] = value
    
    def set_smido_phase(self, phase: str):
        """Update current SMIDO phase"""
        self.smido_phase = phase
    
    def get_context_for_llm(self) -> str:
        """Format W+C for LLM prompts"""
        prompt = "## Current Situation (WorldState - W)\n"
        
        if "current_state" in self.worldstate:
            cs = self.worldstate["current_state"]
            prompt += f"- Room temp: {cs.get('current_room_temp', '?')}°C\n"
            prompt += f"- Hot gas temp: {cs.get('current_hot_gas_temp', '?')}°C\n"
            prompt += f"- Suction temp: {cs.get('current_suction_temp', '?')}°C\n"
            prompt += f"- Liquid temp: {cs.get('current_liquid_temp', '?')}°C\n"
            prompt += f"- Ambient temp: {cs.get('current_ambient_temp', '?')}°C\n"
            prompt += f"- Door open: {cs.get('current_door_open', False)}\n"
        
        if "flags" in self.worldstate:
            flags = self.worldstate["flags"]
            active_flags = [k for k, v in flags.items() if v]
            if active_flags:
                prompt += f"- Active flags: {', '.join(active_flags)}\n"
        
        if "observations" in self.worldstate:
            obs = self.worldstate["observations"]
            if obs:
                prompt += f"- Technician observations: {len(obs)} recorded\n"
        
        prompt += "\n## Installation Design (Context - C)\n"
        
        if "design_parameters" in self.context:
            dp = self.context["design_parameters"]
            prompt += f"- Target temp: {dp.get('target_temp', '?')}°C\n"
            prompt += f"- Design superheat: {dp.get('superheat_design', '?')}K\n"
            prompt += f"- Design subcooling: {dp.get('subcooling_design', '?')}K\n"
            prompt += f"- Evaporator temp design: {dp.get('evaporator_temp_design', '?')}°C\n"
            prompt += f"- Condenser temp design: {dp.get('condenser_temp_design', '?')}°C\n"
        
        if "control_settings" in self.context:
            cs = self.context["control_settings"]
            prompt += f"- Thermostat setpoint: {cs.get('thermostat_setpoint', '?')}°C\n"
            prompt += f"- Defrost interval: {cs.get('defrost_interval_hours', '?')} hours\n"
        
        if "balance_check_parameters" in self.context:
            bcp = self.context["balance_check_parameters"]
            prompt += f"- Hot gas temp range: {bcp.get('hot_gas_temp_min_C', '?')}-{bcp.get('hot_gas_temp_max_C', '?')}°C\n"
            prompt += f"- Suction temp range: {bcp.get('suction_temp_min_C', '?')}-{bcp.get('suction_temp_max_C', '?')}°C\n"
        
        prompt += f"\n## Current SMIDO Phase: {self.smido_phase.upper()}\n"
        
        return prompt
    
    def to_tree_data_environment(self) -> Dict[str, Any]:
        """Export to TreeData.environment format"""
        return {
            "worldstate": self.worldstate,
            "context": self.context,
            "user_input": self.user_input,
            "smido_phase": self.smido_phase,
            "asset_id": self.asset_id
        }
    
    def get_balance_status(self) -> Dict[str, Any]:
        """
        Compare W vs C to determine if system is "uit balans".
        Returns summary of balance check.
        """
        if not self.worldstate or not self.context:
            return {"status": "unknown", "reason": "Missing W or C data"}
        
        current_state = self.worldstate.get("current_state", {})
        design_params = self.context.get("design_parameters", {})
        balance_params = self.context.get("balance_check_parameters", {})
        
        out_of_balance = []
        
        # Room temp check
        current_temp = current_state.get("current_room_temp")
        target_temp = design_params.get("target_temp")
        if current_temp is not None and target_temp is not None:
            deviation = abs(current_temp - target_temp)
            if deviation > 5:
                out_of_balance.append({
                    "factor": "room_temperature",
                    "current": current_temp,
                    "design": target_temp,
                    "deviation": current_temp - target_temp
                })
        
        # Hot gas temp check
        hot_gas = current_state.get("current_hot_gas_temp")
        if hot_gas is not None:
            min_hot_gas = balance_params.get("hot_gas_temp_min_C", 45.0)
            max_hot_gas = balance_params.get("hot_gas_temp_max_C", 65.0)
            if hot_gas < min_hot_gas or hot_gas > max_hot_gas:
                out_of_balance.append({
                    "factor": "hot_gas_temperature",
                    "current": hot_gas,
                    "design_range": f"{min_hot_gas}-{max_hot_gas}"
                })
        
        return {
            "status": "uit_balans" if out_of_balance else "in_balance",
            "out_of_balance_factors": out_of_balance,
            "worldstate_summary": {
                "room_temp": current_temp,
                "hot_gas_temp": hot_gas,
                "suction_temp": current_state.get("current_suction_temp")
            }
        }

