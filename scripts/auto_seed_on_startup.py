#!/usr/bin/env python3
"""
Auto-seed VSM config on first startup if it doesn't exist.
This runs automatically before the main app starts.
"""
import asyncio
import os
import sys

async def check_and_seed():
    """Check if VSM config exists, seed if not."""
    
    # Only run if we have Weaviate connection
    if not os.getenv("WCD_URL") or not os.getenv("WCD_API_KEY"):
        print("⚠️  No Weaviate connection configured, skipping auto-seed")
        return
    
    try:
        from weaviate.classes.query import Filter
        from elysia.util.client import ClientManager
        
        print("🔍 Checking for VSM default config...")
        
        # Check if config exists
        client_manager = ClientManager()
        async with client_manager.connect_to_async_client() as client:
            if not await client.collections.exists("ELYSIA_CONFIG__"):
                print("📦 ELYSIA_CONFIG__ collection doesn't exist")
                needs_seed = True
            else:
                collection = client.collections.get("ELYSIA_CONFIG__")
                default_configs = await collection.query.fetch_objects(
                    filters=Filter.all_of([
                        Filter.by_property("default").equal(True),
                        Filter.by_property("user_id").equal("default_user"),
                    ]),
                    limit=1
                )
                
                needs_seed = len(default_configs.objects) == 0
                
                if not needs_seed:
                    config = default_configs.objects[0].properties
                    config_name = config.get("name", "Unknown")
                    bootstrappers = config.get("feature_bootstrappers", [])
                    print(f"✅ Found existing default config: {config_name}")
                    print(f"   Bootstrappers: {', '.join(bootstrappers) if bootstrappers else 'none'}")
        
        await client_manager.close_clients()
        
        if needs_seed:
            print("🌱 No VSM config found - seeding now...")
            # Import and run the seed script
            sys.path.insert(0, os.path.dirname(__file__))
            from seed_default_config import seed_default_config
            await seed_default_config()
            print("✅ VSM config seeded successfully!")
        else:
            print("✅ VSM config already exists - skipping seed")
            
    except Exception as e:
        print(f"⚠️  Error checking/seeding config: {e}")
        print("   App will continue with default Elysia config")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_and_seed())

