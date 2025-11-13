#!/usr/bin/env python3
"""
Tag UserFacing diagrams with SMIDO phases for findability.

ISSUE: VSM_DiagramUserFacing diagrams have empty smido_phases arrays.
FIX: Populate based on when_to_show field + SMIDO methodology alignment.

Run: python3 scripts/tag_user_facing_diagrams.py
"""

import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from elysia.util.client import ClientManager
from weaviate.classes.query import Filter


# Mapping: diagram_id → SMIDO phases
PHASE_MAPPINGS = {
    "smido_overview": ["M"],  # Overview diagram = Melding phase (starting point)
    "troubleshooting_template": ["M", "T"],  # Early troubleshooting phases
    "diagnose_4ps": ["I", "P1", "P2", "P3", "P4"],  # Diagnose phase (all 4 P's)
    "basic_cycle": ["I"],  # Installation familiarity (understand the system)
    "measurement_points": ["I", "P3"],  # Where to measure (Install + Parameters)
    "system_balance": ["I", "P2", "P3"],  # Balance concept (Install + Settings + Params)
    "pressostat_settings": ["P1", "P2"],  # Pressostat (Power + Settings)
    "frozen_evaporator": ["O"],  # Component troubleshooting (Onderdelen)
}


async def main():
    """Update VSM_DiagramUserFacing objects with SMIDO phase tags."""
    
    print("=" * 60)
    print("Tag UserFacing Diagrams with SMIDO Phases")
    print("=" * 60)
    
    cm = ClientManager()
    
    try:
        async with cm.connect_to_async_client() as client:
            # Check collection exists
            if not await client.collections.exists('VSM_DiagramUserFacing'):
                print("❌ VSM_DiagramUserFacing collection not found!")
                return
            
            coll = client.collections.get('VSM_DiagramUserFacing')
            
            # Get all UserFacing diagrams
            print("\n📊 Fetching all UserFacing diagrams...")
            all_diagrams = await coll.query.fetch_objects(limit=10)
            
            print(f"✅ Found {len(all_diagrams.objects)} diagrams\n")
            
            # Update each diagram
            updated_count = 0
            for obj in all_diagrams.objects:
                diagram_id = obj.properties.get('diagram_id')
                current_phases = obj.properties.get('smido_phases', [])
                
                if diagram_id in PHASE_MAPPINGS:
                    new_phases = PHASE_MAPPINGS[diagram_id]
                    
                    # Update with phase tags
                    await coll.data.update(
                        uuid=obj.uuid,
                        properties={"smido_phases": new_phases}
                    )
                    
                    print(f"✅ {diagram_id:30s} → {new_phases}")
                    updated_count += 1
                else:
                    print(f"⚠️  {diagram_id:30s} → No mapping defined (skipped)")
            
            print(f"\n{'='*60}")
            print(f"✅ Updated {updated_count}/{len(all_diagrams.objects)} diagrams")
            print(f"{'='*60}\n")
            
            # Verify: Query one diagram by SMIDO phase
            print("🔍 Verification: Query diagrams by phase 'M' (Melding)...")
            test_results = await coll.query.fetch_objects(
                filters=Filter.by_property("smido_phases").contains_any(["M"]),
                limit=5
            )
            
            print(f"✅ Found {len(test_results.objects)} diagrams with phase 'M':")
            for obj in test_results.objects:
                print(f"   - {obj.properties.get('diagram_id')}")
            
            print("\n✅ Script complete! UserFacing diagrams now findable by SMIDO phase.")
    
    finally:
        await cm.close_clients()


if __name__ == "__main__":
    asyncio.run(main())

