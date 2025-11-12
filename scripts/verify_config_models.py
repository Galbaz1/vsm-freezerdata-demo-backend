#!/usr/bin/env python3
"""
Verify that the config stored in Weaviate has the correct model configuration.
This decrypts the settings and shows the actual model values.
"""
import asyncio
import json
from dotenv import load_dotenv
load_dotenv()

from elysia.util.client import ClientManager
from elysia.api.utils.encryption import decrypt_api_keys


async def verify_models():
    """Verify model configuration in stored config"""
    print("\n" + "="*80)
    print("VERIFYING MODEL CONFIGURATION IN WEAVIATE")
    print("="*80)

    client_manager = ClientManager()

    async with client_manager.connect_to_async_client() as client:
        collection = client.collections.get("ELYSIA_CONFIG__")

        # Get the default config
        print("\n🔍 Fetching default config...")
        from weaviate.classes.query import Filter
        default_configs = await collection.query.fetch_objects(
            filters=Filter.by_property("default").equal(True),
            limit=1
        )

        if not default_configs.objects:
            print("❌ No default config found!")
            return

        config_obj = default_configs.objects[0]
        props = config_obj.properties

        print(f"✅ Found config: {props.get('name')}")
        print(f"   Config ID: {props.get('config_id')}")
        print(f"   User ID: {props.get('user_id')}")

        # Decrypt settings
        settings = props.get('settings', {})
        if not settings:
            print("\n❌ No settings found in config!")
            return

        print("\n🔓 Decrypting settings...")
        decrypted_settings = decrypt_api_keys(settings)

        # Extract model configuration
        print("\n" + "="*80)
        print("MODEL CONFIGURATION")
        print("="*80)

        base_model = decrypted_settings.get('BASE_MODEL', 'NOT SET')
        complex_model = decrypted_settings.get('COMPLEX_MODEL', 'NOT SET')
        base_provider = decrypted_settings.get('BASE_PROVIDER', 'NOT SET')
        complex_provider = decrypted_settings.get('COMPLEX_PROVIDER', 'NOT SET')

        print(f"\n📊 Base Model:")
        print(f"   Provider: {base_provider}")
        print(f"   Model: {base_model}")
        print(f"   Combined: {base_provider}/{base_model}")

        print(f"\n📊 Complex Model:")
        print(f"   Provider: {complex_provider}")
        print(f"   Model: {complex_model}")
        print(f"   Combined: {complex_provider}/{complex_model}")

        # Verify correctness
        print("\n" + "="*80)
        print("VERIFICATION")
        print("="*80)

        correct_base = (base_provider == "openai" and base_model == "gpt-4.1")
        correct_complex = (complex_provider == "gemini" and complex_model == "gemini-2.5-pro")

        if correct_base:
            print("\n✅ Base model configuration is CORRECT")
            print(f"   → {base_provider}/{base_model}")
        else:
            print(f"\n❌ Base model configuration is WRONG")
            print(f"   Expected: openai/gpt-4.1")
            print(f"   Got: {base_provider}/{base_model}")

        if correct_complex:
            print("\n✅ Complex model configuration is CORRECT")
            print(f"   → {complex_provider}/{complex_model}")
            print("   This will route to Google AI Studio using GOOGLE_API_KEY")
        else:
            print(f"\n❌ Complex model configuration is WRONG")
            print(f"   Expected: gemini/gemini-2.5-pro")
            print(f"   Got: {complex_provider}/{complex_model}")

        # Check agent configuration
        print("\n" + "="*80)
        print("AGENT CONFIGURATION")
        print("="*80)

        agent_desc = props.get('agent_description', '')
        style = props.get('style', '')
        end_goal = props.get('end_goal', '')

        is_vsm = (
            'Virtual Service Mechanic' in agent_desc and
            agent_desc.startswith('Je bent') and
            'junior' in style.lower()
        )

        if is_vsm:
            print("\n✅ Agent configuration is VSM-specific (Dutch)")
            print(f"   Agent: {agent_desc[:80]}...")
            print(f"   Style: {style[:80]}...")
            print(f"   Goal: {end_goal[:80]}...")
        else:
            print("\n❌ Agent configuration is NOT VSM-specific")
            print(f"   Agent: {agent_desc[:80]}...")

        print("\n" + "="*80)
        if correct_base and correct_complex and is_vsm:
            print("✅ ALL CHECKS PASSED - Frontend will load correct config!")
        else:
            print("❌ SOME CHECKS FAILED - Config needs fixing")
        print("="*80 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(verify_models())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
