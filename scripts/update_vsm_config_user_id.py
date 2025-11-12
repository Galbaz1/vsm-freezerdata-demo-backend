#!/usr/bin/env python3
"""
Update the VSM config to use the hashed user ID that the frontend is using.
This ensures the frontend loads the VSM config instead of creating a new one.
"""
import asyncio
from dotenv import load_dotenv
load_dotenv()

from elysia.util.client import ClientManager
from weaviate.classes.query import Filter


async def update_user_id():
    """Update VSM config to use the frontend's user ID"""
    print("\n" + "="*80)
    print("UPDATING VSM CONFIG USER ID")
    print("="*80)

    # The user ID the frontend is using (from your logs)
    frontend_user_id = "d00aac2576b0fa321407bb420641427c"

    client_manager = ClientManager()

    async with client_manager.connect_to_async_client() as client:
        collection = client.collections.get("ELYSIA_CONFIG__")

        # Get the VSM config
        print(f"\n🔍 Finding VSM config...")
        all_configs = await collection.query.fetch_objects(limit=10)

        vsm_config_uuid = None
        for obj in all_configs.objects:
            props = obj.properties
            agent_desc = props.get('agent_description', '')
            if agent_desc.startswith('Je bent') and 'Virtual Service Mechanic' in agent_desc:
                vsm_config_uuid = obj.uuid
                current_user_id = props.get('user_id')
                print(f"   ✅ Found VSM config")
                print(f"   UUID: {obj.uuid}")
                print(f"   Current user_id: {current_user_id}")
                print(f"   Target user_id: {frontend_user_id}")
                break

        if not vsm_config_uuid:
            print("   ❌ VSM config not found!")
            return

        # Update the user_id
        print(f"\n📝 Updating user_id to match frontend session...")
        await collection.data.update(
            uuid=vsm_config_uuid,
            properties={"user_id": frontend_user_id}
        )
        print(f"   ✅ Updated!")

        # Verify
        print(f"\n🔍 Verifying update...")
        updated_obj = await collection.query.fetch_object_by_id(vsm_config_uuid)
        if updated_obj:
            new_user_id = updated_obj.properties.get('user_id')
            if new_user_id == frontend_user_id:
                print(f"   ✅ SUCCESS: user_id is now {new_user_id}")
            else:
                print(f"   ❌ FAILED: user_id is {new_user_id}, expected {frontend_user_id}")
        else:
            print(f"   ❌ Could not verify")

        print("\n" + "="*80)
        print("✅ VSM Config Updated!")
        print("="*80)
        print("""
Now the frontend will find the VSM config because the user_id matches!

Next steps:
1. Refresh the browser (F5) or clear cache
2. The frontend should now load with Dutch VSM instructions
3. Test with: "Hallo, ik ben monteur op locatie"
        """)
        print("="*80 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(update_user_id())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
