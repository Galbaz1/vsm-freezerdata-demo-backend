#!/usr/bin/env python3
"""
Check what the frontend sees when it loads the config.
This mimics what the frontend does when loading the agent configuration.
"""
import asyncio
from dotenv import load_dotenv
load_dotenv()

from elysia.util.client import ClientManager
from weaviate.classes.query import Filter


async def check_frontend_view():
    """Check what config the frontend would load"""
    print("\n" + "="*80)
    print("FRONTEND VIEW: What Config Gets Loaded")
    print("="*80)

    client_manager = ClientManager()

    async with client_manager.connect_to_async_client() as client:
        collection = client.collections.get("ELYSIA_CONFIG__")

        # This is what the frontend does: look for default config
        print("\n🔍 Query 1: Looking for default=True config...")
        default_configs = await collection.query.fetch_objects(
            filters=Filter.by_property("default").equal(True),
            limit=10
        )

        print(f"   Found {len(default_configs.objects)} config(s) with default=True")

        if default_configs.objects:
            for i, obj in enumerate(default_configs.objects, 1):
                props = obj.properties
                print(f"\n{'='*80}")
                print(f"CONFIG #{i} (This is what frontend loads)")
                print(f"{'='*80}")
                print(f"Name: {props.get('name')}")
                print(f"User ID: {props.get('user_id')}")
                print(f"Config ID: {props.get('config_id')}")
                print(f"\n📋 AGENT SECTION (What frontend displays):")
                print(f"\n  Agent Description:")
                agent_desc = props.get('agent_description', '')
                print(f"  {agent_desc[:200]}...")
                print(f"  Language: {'Dutch ✅' if agent_desc.startswith('Je bent') else 'English ❌'}")
                print(f"  Length: {len(agent_desc)} characters")

                print(f"\n  Style:")
                style = props.get('style', '')
                print(f"  {style[:150]}...")
                print(f"  Length: {len(style)} characters")

                print(f"\n  End Goal:")
                end_goal = props.get('end_goal', '')
                print(f"  {end_goal[:150]}...")
                print(f"  Length: {len(end_goal)} characters")

                print(f"\n  Branch Initialization: {props.get('branch_initialisation')}")

        # Also check if there's a user-specific config that might override
        print(f"\n{'='*80}")
        print("🔍 Query 2: Checking for ALL configs (user-specific might override)")
        print(f"{'='*80}")
        all_configs = await collection.query.fetch_objects(limit=10)
        print(f"\n   Total configs in Weaviate: {len(all_configs.objects)}")

        for obj in all_configs.objects:
            props = obj.properties
            print(f"\n   - {props.get('name')} (user={props.get('user_id')}, default={props.get('default')})")

        print("\n" + "="*80)
        print("ANALYSIS")
        print("="*80)

        if len(default_configs.objects) == 1:
            obj = default_configs.objects[0]
            props = obj.properties
            agent_desc = props.get('agent_description', '')
            is_dutch = agent_desc.startswith('Je bent')
            is_vsm = 'Virtual Service Mechanic' in agent_desc

            if is_dutch and is_vsm:
                print("\n✅ Frontend SHOULD load correct Dutch VSM agent")
                print("   If you're seeing English prompts, they might be:")
                print("   1. Collection query suggestions (not agent config)")
                print("   2. Cached from a previous session")
                print("   3. From a different UI section")
            else:
                print("\n❌ Frontend is loading WRONG config!")
                print(f"   Dutch: {is_dutch}")
                print(f"   VSM: {is_vsm}")
        elif len(default_configs.objects) > 1:
            print("\n⚠️  WARNING: Multiple default configs found!")
            print("   Frontend might pick the wrong one")
        else:
            print("\n❌ NO default config found!")
            print("   Frontend will create generic config")

        print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(check_frontend_view())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
