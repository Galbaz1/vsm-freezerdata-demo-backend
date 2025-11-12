#!/usr/bin/env python3
"""
Debug script to check what configs exist in ELYSIA_CONFIG__ collection
and understand why frontend is loading wrong config.
"""
import asyncio
import json
from dotenv import load_dotenv
load_dotenv()

from elysia.util.client import ClientManager


async def debug_configs():
    """Query all configs in ELYSIA_CONFIG__ and show details"""
    print("\n" + "="*80)
    print("FRONTEND CONFIG DEBUG - Querying ELYSIA_CONFIG__ Collection")
    print("="*80)

    client_manager = ClientManager()

    async with client_manager.connect_to_async_client() as client:
        collection = client.collections.get("ELYSIA_CONFIG__")

        # Get ALL configs (no filter)
        print("\n🔍 Fetching ALL configs from Weaviate...")
        all_configs = await collection.query.fetch_objects(limit=100)

        print(f"\n📊 Found {len(all_configs.objects)} config(s) in ELYSIA_CONFIG__\n")

        if not all_configs.objects:
            print("❌ No configs found! This is the problem.")
            return

        # Show each config
        for i, obj in enumerate(all_configs.objects, 1):
            props = obj.properties
            print(f"\n{'='*80}")
            print(f"CONFIG #{i}")
            print(f"{'='*80}")
            print(f"UUID: {obj.uuid}")
            print(f"Name: {props.get('name', 'N/A')}")
            print(f"Config ID: {props.get('config_id', 'N/A')}")
            print(f"User ID: {props.get('user_id', 'N/A')}")
            print(f"Default: {props.get('default', 'N/A')}")
            print(f"\n--- Agent Configuration ---")
            print(f"Agent Description (first 100 chars): {props.get('agent_description', 'N/A')[:100]}...")
            print(f"Style (first 80 chars): {props.get('style', 'N/A')[:80]}...")
            print(f"End Goal (first 80 chars): {props.get('end_goal', 'N/A')[:80]}...")
            print(f"Branch Init: {props.get('branch_initialisation', 'N/A')}")

            # Check settings (encrypted)
            settings = props.get('settings', {})
            if settings:
                print(f"\n--- Model Configuration ---")
                # Settings are encrypted, so we can't see the actual values
                # But we can see if they exist
                print(f"Settings object present: Yes ({len(str(settings))} bytes)")
                # Try to show some info if it's a dict
                if isinstance(settings, dict):
                    print(f"Settings keys: {list(settings.keys())[:5]}...")
                else:
                    print(f"Settings type: {type(settings)}")
            else:
                print("\n--- Model Configuration ---")
                print("❌ No settings found!")

            print(f"\n--- Frontend Config ---")
            frontend_config = props.get('frontend_config', {})
            if frontend_config:
                print(f"Frontend config: {json.dumps(frontend_config, indent=2)}")
            else:
                print("❌ No frontend_config found!")

        # Show which config should be loaded
        print(f"\n{'='*80}")
        print("ANALYSIS")
        print(f"{'='*80}")

        default_configs = [obj for obj in all_configs.objects if obj.properties.get('default') == True]
        print(f"\n✅ Configs with default=True: {len(default_configs)}")

        if default_configs:
            for obj in default_configs:
                props = obj.properties
                print(f"\n  → Config: {props.get('name')}")
                print(f"    User ID: {props.get('user_id')}")
                print(f"    Config ID: {props.get('config_id')}")

        default_user_configs = [obj for obj in all_configs.objects if obj.properties.get('user_id') == 'default_user']
        print(f"\n✅ Configs with user_id='default_user': {len(default_user_configs)}")

        if len(all_configs.objects) > 1:
            print(f"\n⚠️  WARNING: Multiple configs exist ({len(all_configs.objects)} total)")
            print("   Frontend might be loading the wrong one!")

        if len(default_configs) == 0:
            print(f"\n❌ PROBLEM: No config has default=True!")
            print("   Frontend won't know which config to load!")
        elif len(default_configs) > 1:
            print(f"\n⚠️  WARNING: Multiple configs have default=True!")
            print("   This could cause frontend to load the wrong one!")

        print("\n" + "="*80)


if __name__ == "__main__":
    try:
        asyncio.run(debug_configs())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
