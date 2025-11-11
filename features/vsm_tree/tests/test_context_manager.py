#!/usr/bin/env python3
"""
Test script for Context Manager.
"""

import sys
from features.vsm_tree.context_manager import ContextManager


def test_context_manager():
    """Test Context Manager functionality"""
    print("=" * 60)
    print("Context Manager Test")
    print("=" * 60)
    
    try:
        cm = ContextManager()
        
        # Test initialization
        assert cm.smido_phase == "melding", "Initial phase should be 'melding'"
        assert cm.worldstate == {}, "WorldState should be empty initially"
        assert cm.context == {}, "Context should be empty initially"
        print("\n✅ Context Manager initialized correctly")
        
        # Test phase setting
        cm.set_smido_phase("technisch")
        assert cm.smido_phase == "technisch", "Phase should be updated"
        print("✅ Phase setting works")
        
        # Test WorldState update
        test_worldstate = {
            "current_state": {
                "current_room_temp": -28.0,
                "current_hot_gas_temp": 45.0
            },
            "flags": {
                "main_temp_high": True
            }
        }
        cm.update_worldstate(test_worldstate)
        assert "current_state" in cm.worldstate, "WorldState should be updated"
        assert "last_updated" in cm.worldstate, "Last updated timestamp should be added"
        print("✅ WorldState update works")
        
        # Test user observation
        cm.add_user_observation("visual_check", "No obvious defects")
        assert len(cm.worldstate.get("observations", [])) == 1, "Observation should be added"
        print("✅ User observation works")
        
        # Test user input
        cm.add_user_input("system_familiar", True)
        assert cm.user_input.get("system_familiar") == True, "User input should be stored"
        print("✅ User input works")
        
        # Test context loading
        try:
            cm.load_context("135_1570")
            assert "design_parameters" in cm.context, "Context should be loaded"
            assert cm.asset_id == "135_1570", "Asset ID should be set"
            print("✅ Context loading works")
        except FileNotFoundError:
            print("⚠️  Context file not found (expected in some environments)")
        
        # Test balance status
        balance = cm.get_balance_status()
        assert "status" in balance, "Balance status should have status"
        print("✅ Balance status check works")
        
        # Test LLM context formatting
        llm_context = cm.get_context_for_llm()
        assert "Current Situation" in llm_context, "LLM context should include WorldState"
        assert "Installation Design" in llm_context, "LLM context should include Context"
        print("✅ LLM context formatting works")
        
        # Test environment export
        env = cm.to_tree_data_environment()
        assert "worldstate" in env, "Environment should include worldstate"
        assert "context" in env, "Environment should include context"
        assert "smido_phase" in env, "Environment should include smido_phase"
        print("✅ Environment export works")
        
        print("\n✅ All Context Manager tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_context_manager()
    sys.exit(0 if success else 1)

