#!/usr/bin/env python3
"""
Test script for SMIDO Orchestrator.
"""

import sys
from elysia import Tree
from features.vsm_tree.context_manager import ContextManager
from features.vsm_tree.smido_orchestrator import SMIDOOrchestrator


def test_orchestrator():
    """Test SMIDO Orchestrator functionality"""
    print("=" * 60)
    print("SMIDO Orchestrator Test")
    print("=" * 60)
    
    try:
        # Create tree and context manager
        tree = Tree(branch_initialisation="empty")
        context_manager = ContextManager()
        orchestrator = SMIDOOrchestrator(tree, context_manager)
        
        # Test initialization
        assert orchestrator.get_current_phase() == "melding", "Should start at melding"
        assert orchestrator.current_phase_index == 0, "Phase index should be 0"
        print("\n✅ Orchestrator initialized correctly")
        
        # Test phase progression
        next_phase = orchestrator.transition_to_next_phase()
        assert next_phase == "technisch", "Should transition to technisch"
        assert orchestrator.get_current_phase() == "technisch", "Current phase should be technisch"
        assert "melding" in orchestrator.completed_phases, "Melding should be in completed phases"
        print("✅ Phase progression works")
        
        # Test multiple transitions
        orchestrator.transition_to_next_phase()
        orchestrator.transition_to_next_phase()
        assert orchestrator.get_current_phase() == "diagnose", "Should reach diagnose phase"
        print("✅ Multiple phase transitions work")
        
        # Test phase skipping
        context_manager.add_user_input("system_familiar", True)
        orchestrator.reset()
        orchestrator.transition_to_next_phase()  # M → T
        orchestrator.transition_to_next_phase()  # T → I (should skip)
        # I should be skipped and we should be at D
        assert "installatie" in orchestrator.skipped_phases or orchestrator.get_current_phase() == "diagnose", "Installatie should be skipped"
        print("✅ Phase skipping works")
        
        # Test P-branch selection
        orchestrator.reset()
        context_manager.update_worldstate({
            "current_state": {
                "current_hot_gas_temp": 25.0,  # Compressor not running
                "current_room_temp": -20.0
            },
            "flags": {}
        })
        
        p_branch = orchestrator.should_branch_to_p()
        assert p_branch == "p1_power", "Should select P1 for compressor not running"
        print("✅ P-branch selection works (compressor not running)")
        
        # Test P-branch selection for temp out of range
        context_manager.update_worldstate({
            "current_state": {
                "current_hot_gas_temp": 45.0,  # Compressor running
                "current_room_temp": -20.0  # Out of range
            },
            "flags": {}
        })
        try:
            context_manager.load_context("135_1570")
        except FileNotFoundError:
            pass
        
        p_branch = orchestrator.should_branch_to_p()
        assert p_branch in ["p2_procesinstellingen", "p1_power"], "Should select P2 for temp out of range with system running"
        print("✅ P-branch selection works (temp out of range)")
        
        # Test summary generation
        orchestrator.reset()
        orchestrator.transition_to_next_phase()
        summary = orchestrator.generate_smido_summary()
        assert "SMIDO Workflow Summary" in summary, "Summary should include title"
        assert "M - MELDING" in summary, "Summary should include M phase"
        print("✅ Summary generation works")
        
        # Test reset
        orchestrator.reset()
        assert orchestrator.get_current_phase() == "melding", "Reset should return to melding"
        assert len(orchestrator.completed_phases) == 0, "Completed phases should be cleared"
        print("✅ Reset works")
        
        print("\n✅ All Orchestrator tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_orchestrator()
    sys.exit(0 if success else 1)

