#!/usr/bin/env python3
"""
Permanently fix the config issue by:
1. Deleting the wrong "New Config"
2. Keeping only the VSM config
3. Explaining how to prevent this
"""
import asyncio
from dotenv import load_dotenv
load_dotenv()

from elysia.util.client import ClientManager
from weaviate.classes.query import Filter


async def fix_permanently():
    """Delete wrong config and keep only VSM config"""
    print("\n" + "="*80)
    print("PERMANENT FIX: Removing Wrong Config")
    print("="*80)

    client_manager = ClientManager()

    async with client_manager.connect_to_async_client() as client:
        collection = client.collections.get("ELYSIA_CONFIG__")

        # Get all configs
        print("\n🔍 Fetching all configs...")
        all_configs = await collection.query.fetch_objects(limit=10)

        vsm_config = None
        configs_to_delete = []

        for obj in all_configs.objects:
            props = obj.properties
            name = props.get('name', '')
            user_id = props.get('user_id', '')
            agent_desc = props.get('agent_description', '')

            # Identify VSM config (Dutch)
            if agent_desc.startswith('Je bent') and 'Virtual Service Mechanic' in agent_desc:
                vsm_config = obj
                print(f"\n✅ Found VSM config: {name}")
                print(f"   User ID: {user_id}")
                print(f"   UUID: {obj.uuid}")
            else:
                configs_to_delete.append(obj)
                print(f"\n❌ Found wrong config: {name}")
                print(f"   User ID: {user_id}")
                print(f"   UUID: {obj.uuid}")
                print(f"   Agent: {agent_desc[:50]}...")

        # Delete wrong configs
        if configs_to_delete:
            print(f"\n🗑️  Deleting {len(configs_to_delete)} wrong config(s)...")
            for obj in configs_to_delete:
                await collection.data.delete_by_id(obj.uuid)
                print(f"   ✅ Deleted: {obj.properties.get('name')}")
        else:
            print("\n✅ No wrong configs to delete")

        # Verify only VSM config remains
        print("\n🔍 Verifying final state...")
        final_configs = await collection.query.fetch_objects(limit=10)
        print(f"   Total configs remaining: {len(final_configs.objects)}")

        if len(final_configs.objects) == 1:
            obj = final_configs.objects[0]
            props = obj.properties
            agent_desc = props.get('agent_description', '')
            if agent_desc.startswith('Je bent'):
                print("\n✅ SUCCESS: Only VSM config remains!")
                print(f"   Name: {props.get('name')}")
                print(f"   User ID: {props.get('user_id')}")
                print(f"   Default: {props.get('default')}")
                print(f"   Agent: Dutch VSM ✅")
            else:
                print("\n❌ Wrong config remains!")
        else:
            print(f"\n⚠️  Warning: {len(final_configs.objects)} configs remain")

        print("\n" + "="*80)
        print("IMPORTANT: How to Prevent This")
        print("="*80)
        print("""
The frontend keeps creating new configs because it uses a hashed user ID
that changes per session.

To prevent this:
1. Clear your browser cache/cookies before restarting frontend
2. Or: Use incognito mode to test fresh session
3. Or: Frontend needs to be modified to not auto-create configs

For now, after this fix:
- Restart Elysia: elysia start
- Clear browser cache
- Open frontend in incognito mode
- It should load the VSM config correctly
        """)
        print("="*80 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(fix_permanently())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
