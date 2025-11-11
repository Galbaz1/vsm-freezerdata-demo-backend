#!/usr/bin/env python3
"""
Test script for integrated VSM tree with orchestrator and context manager.
"""

import sys
from features.vsm_tree.smido_tree import create_vsm_tree


def test_integrated_tree():
    """Test integrated tree creation with orchestrator"""
    print("=" * 60)
    print("Integrated VSM Tree Test")
    print("=" * 60)
    
    try:
        # Test basic tree creation (without orchestrator)
        tree = create_vsm_tree()
        assert tree is not None, "Tree should be created"
        print("\n✅ Basic tree creation works")
        
        # Test tree with orchestrator
        tree, orchestrator, context = create_vsm_tree(
            with_orchestrator=True,
            asset_id="135_1570"
        )
        
        assert tree is not None, "Tree should be created"
        assert orchestrator is not None, "Orchestrator should be created"
        assert context is not None, "Context manager should be created"
        print("✅ Tree with orchestrator creation works")
        
        # Test orchestrator phase
        assert orchestrator.get_current_phase() == "melding", "Should start at melding"
        print("✅ Orchestrator phase tracking works")
        
        # Test context manager
        assert context.smido_phase == "melding", "Context should track phase"
        if context.context:
            assert "design_parameters" in context.context, "Context should have design parameters"
        print("✅ Context manager integration works")
        
        # Test phase progression
        next_phase = orchestrator.transition_to_next_phase()
        assert next_phase == "technisch", "Should transition to technisch"
        assert context.smido_phase == "technisch", "Context should update phase"
        print("✅ Phase progression with context update works")
        
        # Test summary
        summary = orchestrator.generate_smido_summary()
        assert "SMIDO Workflow Summary" in summary, "Summary should be generated"
        print("✅ Summary generation works")
        
        print("\n✅ All integrated tree tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_integrated_tree()
    sys.exit(0 if success else 1)

