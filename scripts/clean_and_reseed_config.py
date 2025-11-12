#!/usr/bin/env python3
"""
Clean up ALL configs in ELYSIA_CONFIG__ and reseed with correct VSM config.
This fixes the issue where multiple configs with default=True exist.
"""
import asyncio
from dotenv import load_dotenv
load_dotenv()

from elysia.util.client import ClientManager


async def clean_all_configs():
    """Delete ALL configs from ELYSIA_CONFIG__ collection"""
    print("\n" + "="*80)
    print("CLEANING ALL CONFIGS")
    print("="*80)

    client_manager = ClientManager()

    async with client_manager.connect_to_async_client() as client:
        collection = client.collections.get("ELYSIA_CONFIG__")

        # Get ALL configs
        print("\n🔍 Fetching all configs...")
        all_configs = await collection.query.fetch_objects(limit=100)
        print(f"   Found {len(all_configs.objects)} config(s)")

        if not all_configs.objects:
            print("   ✅ No configs to delete")
            return

        # Delete each one
        print("\n🗑️  Deleting all configs...")
        for i, obj in enumerate(all_configs.objects, 1):
            props = obj.properties
            config_name = props.get('name', 'Unknown')
            user_id = props.get('user_id', 'Unknown')
            default = props.get('default', False)

            await collection.data.delete_by_id(obj.uuid)
            print(f"   ✅ Deleted #{i}: {config_name} (user={user_id}, default={default})")

        print(f"\n✅ Deleted {len(all_configs.objects)} config(s)")

        # Verify deletion
        verify = await collection.query.fetch_objects(limit=10)
        if len(verify.objects) == 0:
            print("   ✅ Verified: Collection is now empty")
        else:
            print(f"   ⚠️  Warning: Still found {len(verify.objects)} configs")


async def main():
    """Main function"""
    try:
        await clean_all_configs()

        print("\n" + "="*80)
        print("✅ CLEANUP COMPLETE!")
        print("="*80)
        print("\n📝 Next step: Run the seed script to create fresh VSM config:")
        print("   python3 scripts/seed_default_config.py")
        print("\nThis will create a clean, single config that the frontend will load.")
        print("="*80 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
