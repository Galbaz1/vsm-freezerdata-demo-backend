#!/usr/bin/env python3
"""
Cleanup ELYSIA_CONFIG__ collection - remove old/duplicate configs.

Keeps only:
- Latest default config for default_user (ID: 748ca511-7b03-4217-8da1-140159a8d970)
  
Deletes:
- Old VSM configs for default_user (3 configs with default=False)
- Generic config for user d00aac2576b0fa321407bb420641427c (wrong settings)
"""
import asyncio
from elysia.util.client import ClientManager
from weaviate.util import generate_uuid5

async def cleanup_configs():
    print("🧹 ELYSIA_CONFIG__ Cleanup Script")
    print("=" * 60)
    
    # Config IDs to delete
    configs_to_delete = [
        "0c58102c-d03f-46cb-852d-0bdb26adbb57",  # Old VSM config (default=False, COMPLEX_PROVIDER=google)
        "a78aaa47-30f0-4ac6-a0cc-4b6090508c8d",  # Old VSM config (default=False, gemini/ prefix)
        "aef9ed9f-e114-47c9-9316-1323abc18aa0",  # Old VSM config (default=False, gemini/ prefix)
        "9e516a0b-4cd3-497f-a06e-504550ea726b",  # Generic config (wrong user, wrong settings)
    ]
    
    config_to_keep = "748ca511-7b03-4217-8da1-140159a8d970"  # Latest VSM config (default=True, COMPLEX_PROVIDER=gemini)
    
    client_manager = ClientManager()
    async with client_manager.connect_to_async_client() as client:
        collection = client.collections.get("ELYSIA_CONFIG__")
        
        # Verify the config we want to keep exists
        keep_uuid = generate_uuid5(config_to_keep)
        keep_obj = await collection.query.fetch_object_by_id(uuid=keep_uuid)
        
        if not keep_obj:
            print(f"\n❌ ERROR: Config to keep ({config_to_keep}) not found!")
            print("   Aborting cleanup to avoid data loss.")
            return
        
        print(f"\n✅ Verified config to keep:")
        print(f"   ID: {config_to_keep}")
        print(f"   Name: {keep_obj.properties.get('name', 'N/A')}")
        print(f"   User ID: {keep_obj.properties.get('user_id', 'N/A')}")
        print(f"   Default: {keep_obj.properties.get('default', 'N/A')}")
        
        # Delete old configs
        print(f"\n🗑️  Deleting {len(configs_to_delete)} old/incorrect configs...")
        deleted_count = 0
        
        for config_id in configs_to_delete:
            try:
                uuid = generate_uuid5(config_id)
                
                # Check if exists first
                obj = await collection.query.fetch_object_by_id(uuid=uuid)
                if obj:
                    await collection.data.delete_by_id(uuid)
                    print(f"   ✅ Deleted: {config_id}")
                    print(f"      Name: {obj.properties.get('name', 'N/A')}")
                    print(f"      User: {obj.properties.get('user_id', 'N/A')}")
                    deleted_count += 1
                else:
                    print(f"   ⏭️  Skipped (not found): {config_id}")
            except Exception as e:
                print(f"   ❌ Error deleting {config_id}: {e}")
        
        # Verify final state
        print(f"\n🔍 Verifying final state...")
        all_configs = await collection.query.fetch_objects(limit=100)
        print(f"   Total configs remaining: {len(all_configs.objects)}")
        
        for obj in all_configs.objects:
            props = obj.properties
            print(f"\n   Config: {props.get('name', 'N/A')}")
            print(f"      ID: {props.get('config_id', 'N/A')}")
            print(f"      User: {props.get('user_id', 'N/A')}")
            print(f"      Default: {props.get('default', 'N/A')}")
            print(f"      COMPLEX_PROVIDER: {props.get('settings', {}).get('COMPLEX_PROVIDER', 'N/A')}")
        
        print("\n" + "=" * 60)
        print(f"✅ Cleanup complete!")
        print(f"   Deleted: {deleted_count} configs")
        print(f"   Remaining: {len(all_configs.objects)} config(s)")
        print("=" * 60)
        print("\n🔄 Next steps:")
        print("   1. Apply the fallback fix to elysia/api/routes/init.py")
        print("   2. Restart Elysia: elysia start")
        print("   3. Clear browser cache and reload frontend")
        print("   4. Verify VSM config is loaded correctly")

if __name__ == "__main__":
    try:
        asyncio.run(cleanup_configs())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
