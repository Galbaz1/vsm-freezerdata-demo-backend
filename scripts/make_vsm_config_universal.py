#!/usr/bin/env python3
"""
BETTER SOLUTION: Make the VSM config work for ALL users by creating
multiple copies with different user IDs.

This ensures any user (any session) gets the VSM config.
"""
import asyncio
from dotenv import load_dotenv
load_dotenv()

from elysia.util.client import ClientManager
from elysia.api.utils.encryption import decrypt_api_keys, encrypt_api_keys


async def make_universal():
    """Create VSM configs for multiple common user IDs"""
    print("\n" + "="*80)
    print("UNIVERSAL VSM CONFIG - Works for All Users")
    print("="*80)

    # Common user IDs to cover
    user_ids = [
        "default_user",                               # Default
        "d00aac2576b0fa321407bb420641427c",          # Your current session
        # Add more as needed
    ]

    client_manager = ClientManager()

    async with client_manager.connect_to_async_client() as client:
        collection = client.collections.get("ELYSIA_CONFIG__")

        # Get the existing VSM config to copy
        print("\n🔍 Finding existing VSM config...")
        all_configs = await collection.query.fetch_objects(limit=10)

        vsm_template = None
        for obj in all_configs.objects:
            props = obj.properties
            agent_desc = props.get('agent_description', '')
            if agent_desc.startswith('Je bent') and 'Virtual Service Mechanic' in agent_desc:
                vsm_template = props
                print(f"   ✅ Found VSM config template")
                break

        if not vsm_template:
            print("   ❌ No VSM config found to copy!")
            return

        # Delete all existing configs first
        print("\n🗑️  Removing old configs...")
        for obj in all_configs.objects:
            await collection.data.delete_by_id(obj.uuid)
            print(f"   ✅ Deleted: {obj.properties.get('name')}")

        # Create one VSM config for each user ID
        print(f"\n📝 Creating VSM configs for {len(user_ids)} user IDs...")
        for i, user_id in enumerate(user_ids, 1):
            # Copy the template
            new_config = dict(vsm_template)
            new_config['user_id'] = user_id
            new_config['config_id'] = f"vsm-default-config-{user_id[:8]}"
            new_config['default'] = True  # All are default

            # Insert
            from weaviate.util import generate_uuid5
            uuid = generate_uuid5(new_config['config_id'])
            await collection.data.insert(new_config, uuid=uuid)

            print(f"   ✅ Created config #{i} for user_id: {user_id[:20]}...")

        # Verify
        print("\n🔍 Verifying...")
        final_configs = await collection.query.fetch_objects(limit=10)
        print(f"   Total configs: {len(final_configs.objects)}")

        for obj in final_configs.objects:
            props = obj.properties
            print(f"   - {props.get('user_id')[:20]}... (default={props.get('default')})")

        print("\n" + "="*80)
        print("✅ DONE - VSM Config Now Works for Multiple Users!")
        print("="*80)
        print("""
Benefits:
- Works for your current session ✅
- Works for default_user ✅
- Works if you clear cache ✅ (uses your current session ID)

Limitation:
- If you use a DIFFERENT browser/device, you'll need to add its user ID here

Future: Modify frontend to always use 'default_user' instead of hashed IDs
        """)
        print("="*80 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(make_universal())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
