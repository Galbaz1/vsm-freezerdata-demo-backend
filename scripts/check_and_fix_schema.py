#!/usr/bin/env python3
"""
Check and fix ELYSIA_CONFIG__ schema.
The branch_initialisation property might have wrong data type (TEXT_ARRAY instead of TEXT).
"""
import asyncio
from dotenv import load_dotenv

load_dotenv()

from elysia.util.client import ClientManager


async def check_schema():
    """Check the current schema of ELYSIA_CONFIG__ collection."""
    
    print("🔍 Checking ELYSIA_CONFIG__ Schema...")
    print("=" * 60)
    
    client_manager = ClientManager()
    
    async with client_manager.connect_to_async_client() as client:
        if not await client.collections.exists("ELYSIA_CONFIG__"):
            print("❌ ELYSIA_CONFIG__ collection does not exist!")
            return
        
        collection = client.collections.get("ELYSIA_CONFIG__")
        
        # Get schema
        schema_config = await collection.config.get(simple=False)
        schema_dict = schema_config.to_dict()
        
        print("\n📋 Current Properties:")
        print("-" * 60)
        
        properties = schema_dict.get("properties", [])
        
        for prop in properties:
            # Access property attributes
            name = prop.name if hasattr(prop, "name") else prop.get("name")
            data_type = prop.data_type if hasattr(prop, "data_type") else prop.get("dataType")
            
            # Check for problematic properties
            if name in ["branch_initialisation", "feature_bootstrappers", "use_elysia_collections"]:
                print(f"   🔑 {name}:")
                print(f"      Type: {data_type}")
                
                # Flag issues
                if name == "branch_initialisation" and data_type != "text":
                    print(f"      ❌ WRONG TYPE! Should be 'text', got '{data_type}'")
                elif name == "feature_bootstrappers" and data_type != "text[]":
                    print(f"      ❌ WRONG TYPE! Should be 'text[]', got '{data_type}'")
                elif name == "use_elysia_collections" and data_type != "boolean":
                    print(f"      ❌ WRONG TYPE! Should be 'boolean', got '{data_type}'")
                else:
                    print(f"      ✅ Correct type")
        
        print("\n" + "=" * 60)
        print("\n📝 Checking stored config values...")
        
        # Check actual stored values
        result = await collection.query.fetch_objects(limit=1)
        
        if result.objects:
            config = result.objects[0].properties
            print(f"\n   branch_initialisation: {config.get('branch_initialisation')} (type: {type(config.get('branch_initialisation')).__name__})")
            print(f"   feature_bootstrappers: {config.get('feature_bootstrappers')} (type: {type(config.get('feature_bootstrappers')).__name__})")
            print(f"   use_elysia_collections: {config.get('use_elysia_collections')} (type: {type(config.get('use_elysia_collections')).__name__})")
        
        print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(check_schema())

