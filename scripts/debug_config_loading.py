#!/usr/bin/env python3
"""
Debug config loading from Weaviate to identify where values get swapped.
"""
import asyncio
import json
from dotenv import load_dotenv
from weaviate.classes.query import Filter

load_dotenv()

from elysia.util.client import ClientManager
from elysia.api.utils.config import Config
from elysia.api.utils.encryption import decrypt_api_keys


async def debug_config_loading():
    """Debug the config loading process step by step."""
    
    print("🔍 Debugging Config Loading from Weaviate...")
    print("=" * 80)
    
    client_manager = ClientManager()
    
    async with client_manager.connect_to_async_client() as client:
        collection = client.collections.get("ELYSIA_CONFIG__")
        
        # Fetch the default config
        default_configs = await collection.query.fetch_objects(
            filters=Filter.all_of([
                Filter.by_property("default").equal(True),
                Filter.by_property("user_id").equal("default_user"),
            ])
        )
        
        if not default_configs.objects:
            print("❌ No default config found!")
            return
        
        print("\n📦 Step 1: Raw Weaviate Object Properties")
        print("-" * 80)
        
        raw_props = default_configs.objects[0].properties
        
        # Show the exact values as stored in Weaviate
        print(f"\nbranch_initialisation (raw):")
        print(f"  Value: {raw_props.get('branch_initialisation')}")
        print(f"  Type: {type(raw_props.get('branch_initialisation'))}")
        
        print(f"\nfeature_bootstrappers (raw):")
        print(f"  Value: {raw_props.get('feature_bootstrappers')}")
        print(f"  Type: {type(raw_props.get('feature_bootstrappers'))}")
        
        print(f"\nuse_elysia_collections (raw):")
        print(f"  Value: {raw_props.get('use_elysia_collections')}")
        print(f"  Type: {type(raw_props.get('use_elysia_collections'))}")
        
        print("\n" + "=" * 80)
        print("\n📝 Step 2: After Decryption (if applicable)")
        print("-" * 80)
        
        # Decrypt API keys
        try:
            raw_props["settings"] = decrypt_api_keys(raw_props["settings"])
            print("✅ API keys decrypted")
        except Exception as e:
            print(f"⚠️  Decryption skipped: {e}")
        
        # Show the dict that will be passed to Config.from_json
        print(f"\nbranch_initialisation:")
        print(f"  Value: {raw_props.get('branch_initialisation')}")
        print(f"  Type: {type(raw_props.get('branch_initialisation'))}")
        
        print(f"\nfeature_bootstrappers:")
        print(f"  Value: {raw_props.get('feature_bootstrappers')}")
        print(f"  Type: {type(raw_props.get('feature_bootstrappers'))}")
        
        print("\n" + "=" * 80)
        print("\n🔄 Step 3: After Config.from_json()")
        print("-" * 80)
        
        # Load via Config.from_json
        config = Config.from_json(raw_props)
        
        print(f"\nconfig.branch_initialisation:")
        print(f"  Value: {config.branch_initialisation}")
        print(f"  Type: {type(config.branch_initialisation)}")
        
        print(f"\nconfig.feature_bootstrappers:")
        print(f"  Value: {config.feature_bootstrappers}")
        print(f"  Type: {type(config.feature_bootstrappers)}")
        
        print(f"\nconfig.use_elysia_collections:")
        print(f"  Value: {config.use_elysia_collections}")
        print(f"  Type: {type(config.use_elysia_collections)}")
        
        print("\n" + "=" * 80)
        print("\n📤 Step 4: After config.to_json()")
        print("-" * 80)
        
        # Convert back to JSON (as sent to frontend)
        config_json = config.to_json()
        
        print(f"\nbranch_initialisation:")
        print(f"  Value: {config_json.get('branch_initialisation')}")
        print(f"  Type: {type(config_json.get('branch_initialisation'))}")
        
        print(f"\nfeature_bootstrappers:")
        print(f"  Value: {config_json.get('feature_bootstrappers')}")
        print(f"  Type: {type(config_json.get('feature_bootstrappers'))}")
        
        print(f"\nuse_elysia_collections:")
        print(f"  Value: {config_json.get('use_elysia_collections')}")
        print(f"  Type: {type(config_json.get('use_elysia_collections'))}")
        
        print("\n" + "=" * 80)
        print("\n🎯 DIAGNOSIS:")
        print("-" * 80)
        
        # Check if values match expectations
        if config.branch_initialisation == "empty":
            print("✅ branch_initialisation is correct ('empty')")
        else:
            print(f"❌ branch_initialisation is WRONG: {config.branch_initialisation}")
        
        if config.feature_bootstrappers == ["vsm_smido"]:
            print("✅ feature_bootstrappers is correct (['vsm_smido'])")
        else:
            print(f"❌ feature_bootstrappers is WRONG: {config.feature_bootstrappers}")
        
        if config.use_elysia_collections == True:
            print("✅ use_elysia_collections is correct (True)")
        else:
            print(f"❌ use_elysia_collections is WRONG: {config.use_elysia_collections}")
        
        print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(debug_config_loading())

