#!/usr/bin/env python3
"""
Generate Dutch starter prompts for VSM collections and update ELYSIA_METADATA__.

These prompts appear on the homepage when opening a new chat.
They should be in Dutch and SMIDO-relevant for VSM demo.
"""
import asyncio
from elysia.util.client import ClientManager
from weaviate.classes.query import Filter

# Dutch starter prompts per collection (SMIDO-focused)
DUTCH_PROMPTS = {
    "VSM_ManualSections": [
        "Wat zijn veelvoorkomende oorzaken van compressor storingen?",
        "Welke SMIDO stappen behandelen koudemiddel lekkages?",
        "Wat zijn oplossingen voor slecht ontdooien?",
        "Welke veiligheidsmaatregelen gelden bij onderhoud?",
        "Hoe herken ik een verstopte filterdroger?",
        "Wat is het effect van buitentemperatuur op prestaties?",
        "Wat is COP en hoe verbeter je deze?",
        "Welke componenten hebben de meeste storingen?",
    ],
    "VSM_TelemetryEvent": [
        "Welke 'uit balans' patronen zijn er historisch gezien?",
        "Hoe vaak komt 'ingevroren verdamper' voor?",
        "Wat zijn typische temperaturen bij critical events?",
        "Welke componenten falen het vaakst?",
        "Hoe beïnvloedt deur-open ratio de kamertemperatuur?",
    ],
    "VSM_DiagramUserFacing": [
        "Toon het SMIDO overzichtsdiagram",
        "Welke diagrams helpen bij verdamper problemen?",
        "Wat toont het Diagnose 4P's diagram?",
        "Welke schemas zijn relevant voor procesparameters?",
    ],
    "VSM_DiagramAgentInternal": [
        "Welke SMIDO fases behandelen 'koelproces uit balans'?",
        "Hoe helpt het instrumentatie schema bij P3 diagnose?",
        "Wat zijn de stappen bij bevroren verdamper troubleshooting?",
        "Welke diagrams tonen LP en HP pressostaat instellingen?",
    ],
    "VSM_WorldStateSnapshot": [
        "Wat zijn typische symptomen van 'expansieventiel defect'?",
        "Welke balansfactoren horen bij 'vuile condensor'?",
        "Hoe beïnvloedt deurgebruik de koelprestatie?",
        "Wat is de compressor health score bij normale werking?",
    ],
    "VSM_VlogCase": [
        "Wat zijn veelvoorkomende hoofdoorzaken van koelcel storingen?",
        "Welke SMIDO stappen worden het meest gebruikt?",
        "Hoe los je een bevroren verdamper op (A3)?",
        "Wat zijn oplossingen voor temperatuurregeling problemen?",
    ],
    "VSM_VlogClip": [
        "Wat zijn veelvoorkomende oorzaken van verdamper bevriezen?",
        "Welke componenten falen het vaakst?",
        "Wat zijn de stappen bij expansieventiel defect?",
        "Hoe los je 'onvoldoende warmteafvoer' problemen op?",
    ],
    "FD_Assets": [
        "Toon details van vriezer 135-1570",
        "Wat is de doeltemperatuur van deze installatie?",
        "Welke ontwerp parameters zijn gedefinieerd?",
        "Wat zijn de operationele limieten?",
    ],
}

async def main():
    print("=" * 80)
    print("Updating ELYSIA_METADATA__ with Dutch Starter Prompts")
    print("=" * 80)
    
    cm = ClientManager()
    async with cm.connect_to_async_client() as client:
        coll = client.collections.get('ELYSIA_METADATA__')
        
        # Get all metadata objects
        result = await coll.query.fetch_objects(limit=20)
        
        print(f"\nFound {len(result.objects)} collection metadata objects")
        
        updated_count = 0
        for obj in result.objects:
            collection_name = obj.properties.get('name')
            
            if collection_name in DUTCH_PROMPTS:
                dutch_prompts = DUTCH_PROMPTS[collection_name]
                
                print(f"\nUpdating {collection_name}:")
                print(f"  New prompts: {len(dutch_prompts)}")
                for i, p in enumerate(dutch_prompts[:3], 1):
                    print(f"    {i}. {p}")
                if len(dutch_prompts) > 3:
                    print(f"    ... ({len(dutch_prompts) - 3} more)")
                
                # Update the object (async)
                await coll.data.update(
                    uuid=obj.uuid,
                    properties={"prompts": dutch_prompts}
                )
                
                updated_count += 1
        
        print(f"\n" + "=" * 80)
        print(f"✅ Updated {updated_count} collections with Dutch prompts")
        print("=" * 80)
        
        # Verify
        print("\nVerification:")
        result_verify = await coll.query.fetch_objects(
            filters=Filter.by_property("name").equal("VSM_ManualSections"),
            limit=1
        )
        
        if result_verify.objects:
            prompts = result_verify.objects[0].properties.get('prompts', [])
            print(f"VSM_ManualSections now has {len(prompts)} prompts:")
            for p in prompts[:3]:
                print(f"  - {p}")
    
    await cm.close_clients()
    print("\n✅ Complete! Refresh frontend to see Dutch suggestions.")

if __name__ == "__main__":
    asyncio.run(main())

