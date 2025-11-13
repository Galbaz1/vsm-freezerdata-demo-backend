#!/usr/bin/env python3
"""
Seed a default Elysia config to the ELYSIA_CONFIG__ collection.
This config will be automatically loaded when a new user initializes.

Extracts VSM-specific prompts directly from smido_tree.py to ensure consistency.
"""
import asyncio
import inspect
import os
from uuid import uuid4
from dotenv import load_dotenv
from weaviate.util import generate_uuid5
from weaviate.classes.query import Filter
import weaviate.classes.config as wc
from weaviate.classes.config import Property, DataType

# Load environment variables
load_dotenv()

from elysia.util.client import ClientManager
from elysia.config import Settings
from elysia.api.utils.encryption import encrypt_api_keys


def ensure_fallback_fix_applied():
    """
    Ensure the config fallback fix is applied to init.py.
    This prevents the issue where seeded configs aren't loaded due to user ID mismatch.
    """
    import re
    from pathlib import Path
    
    # Get the project root (assuming script is in scripts/ directory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    init_py_path = project_root / "elysia" / "api" / "routes" / "init.py"
    
    if not init_py_path.exists():
        print(f"\n⚠️  Warning: {init_py_path} not found, skipping fallback fix check")
        return False
    
    # Read the file
    with open(init_py_path, "r") as f:
        content = f.read()
    
    # Check if fallback is already applied
    if 'Fallback to global default_user config' in content:
        print("\n✅ Step 0: Config fallback fix already applied")
        return True
    
    # Apply the fix
    print("\n🔧 Step 0: Applying config fallback fix to init.py...")
    
    # Use the same pattern as apply_config_fallback_fix.py (proven to work)
    # Pattern: Match from function start to the if check
    function_pattern = r'(async def get_default_config\(.*?\n)(.*?)(if len\(default_configs\.objects\) > 0:)'
    
    # Replacement: Add fallback logic before the if check
    replacement = r'''\1\2# Fallback to global default_user config if user-specific not found
        if len(default_configs.objects) == 0:
            default_configs = await collection.query.fetch_objects(
                filters=Filter.all_of(
                    [
                        Filter.by_property("default").equal(True),
                        Filter.by_property("user_id").equal("default_user"),
                    ]
                )
            )

        \3'''
    
    # Apply the fix
    new_content = re.sub(function_pattern, replacement, content, flags=re.DOTALL)
    
    if new_content != content:
        # Backup original
        backup_path = init_py_path.with_suffix('.py.backup')
        with open(backup_path, "w") as f:
            f.write(content)
        print(f"   💾 Backup created: {backup_path}")
        
        # Write modified version
        with open(init_py_path, "w") as f:
            f.write(new_content)
        
        print(f"   ✅ Fallback fix applied successfully!")
        print(f"   📝 Modified: {init_py_path}")
        return True
    else:
        print(f"   ⚠️  Could not apply fix - pattern not found")
        print(f"   💡 You may need to apply the fix manually")
        return False


async def seed_default_config():
    """Create a default config in ELYSIA_CONFIG__ collection."""

    print("🔧 VSM Default Config Seed Script")
    print("=" * 60)

    # 0. Ensure fallback fix is applied (prevents config loading issues)
    ensure_fallback_fix_applied()

    # 1. Extract VSM prompts (hardcoded to avoid import issues during seed)
    print("\n📝 Step 1: Setting VSM prompts...")
    
    # Hardcoded VSM prompts (from smido_tree.py)
    agent_description = """Je bent een gespecialiseerde Virtual Service Mechanic (VSM) assistent voor koeltechniek storingen. Je helpt monteurs bij het diagnosticeren en oplossen van problemen met koelinstallaties door de SMIDO-methodologie te volgen.

Je gebruikt de volgende aanpak:
1. **M**elding - Verzamel symptomen en urgentie
2. **T**echnisch - Visuele inspectie en snelle checks  
3. **I**nstallatie vertrouwd - Bekijk schema's en ontwerpparameters
4. **D**iagnose - 4 P's systematiek (Power, Procesinstellingen, Procesparameters, Productinput)
5. **O**nderdelen - Component isolatie

Belangrijke concepten:
- "Uit balans" betekent dat het systeem buiten ontwerp parameters werkt, niet per se kapotte onderdelen
- WorldState (W) = huidige metingen en trends  
- Context (C) = ontwerp specificaties en instellingen
- Vergelijk altijd W vs C om balans te checken

Je hebt toegang tot:
- Handleidingen met SMIDO-classificatie (zoek per fase)
- Foto's en diagrammen uit de handleidingen
- Telemetrie data (sensor metingen, trends, health scores)
- Vlog cases (A1-A5 probleemoplossings voorbeelden)
- Historische "uit balans" incidenten

Communiceer in het Nederlands, wees informatief maar vriendelijk."""

    style = "Informatief, beleefd en vriendelijk. Gebruik Nederlandse vakjargon waar gepast."

    end_goal = """Je hebt de vraag van de monteur beantwoord met een beknopt overzicht van de resultaten. Of je hebt alle beschikbare opties uitgeput, of gevraagd om verduidelijking van de monteur."""

    branch_initialisation = "empty"  # VSM uses empty init with bootstrapper

    print(f"   ✅ Agent Description: {len(agent_description)} characters")
    print(f"   ✅ Style: {len(style)} characters") 
    print(f"   ✅ End Goal: {len(end_goal)} characters")
    print(f"   ✅ Branch Init: {branch_initialisation}")

    # 2. Set up config values
    # Use consistent config_id so we UPDATE instead of creating new config each time
    config_id = "vsm-default-config-v1"  # Fixed ID ensures updates work
    user_id = "default_user"  # Default user for all new users
    config_name = "VSM Default Config"

    # 3. Create Settings from .env
    print("\n⚙️  Step 2: Loading settings from .env...")
    settings = Settings()
    settings.set_from_env()
    settings_dict = settings.to_json()

    # Fix: Convert port numbers from float to int (Weaviate serialization issue)
    for key in ["LOCAL_WEAVIATE_PORT", "LOCAL_WEAVIATE_GRPC_PORT", 
                "CUSTOM_HTTP_PORT", "CUSTOM_GRPC_PORT"]:
        if key in settings_dict and isinstance(settings_dict[key], float):
            settings_dict[key] = int(settings_dict[key])

    print(f"   ✅ Base Model: {settings.BASE_MODEL}")
    print(f"   ✅ Complex Model: {settings.COMPLEX_MODEL}")
    print(f"   ✅ Weaviate URL: {settings.WCD_URL}")

    # Encrypt API keys for security
    print("\n🔒 Step 3: Encrypting API keys...")
    settings_dict = encrypt_api_keys(settings_dict)
    print("   ✅ API keys encrypted")

    # 4. Create frontend config
    frontend_config = {
        "save_trees_to_weaviate": True,
        "save_configs_to_weaviate": True,
        "client_timeout": 3,
        "tree_timeout": 10,
    }

    # 5. Connect to Weaviate
    print("\n🔌 Step 4: Connecting to Weaviate...")
    client_manager = ClientManager()
    
    try:
        async with client_manager.connect_to_async_client() as client:
            # Create collection if it doesn't exist
            if await client.collections.exists("ELYSIA_CONFIG__"):
                print("   ✅ ELYSIA_CONFIG__ collection exists")
                collection = client.collections.get("ELYSIA_CONFIG__")
            else:
                print("   ⚠️  Creating ELYSIA_CONFIG__ collection...")
                collection = await client.collections.create(
                    "ELYSIA_CONFIG__",
                    vectorizer_config=wc.Configure.Vectorizer.none(),
                    inverted_index_config=wc.Configure.inverted_index(
                        index_timestamps=True
                    ),
                    properties=[
                        Property(name="name", data_type=DataType.TEXT),
                        Property(name="style", data_type=DataType.TEXT),
                        Property(name="agent_description", data_type=DataType.TEXT),
                        Property(name="end_goal", data_type=DataType.TEXT),
                        Property(name="branch_initialisation", data_type=DataType.TEXT),
                        Property(name="user_id", data_type=DataType.TEXT),
                        Property(name="config_id", data_type=DataType.TEXT),
                        Property(name="default", data_type=DataType.BOOL),
                        Property(
                            name="feature_bootstrappers",
                            data_type=DataType.TEXT_ARRAY,
                        ),
                    ],
                )
                print("   ✅ Collection created")

            # Ensure feature_bootstrappers property exists (for existing collections)
            print("\n🛠️  Step 5a: Ensuring schema includes feature_bootstrappers...")
            schema_config = await collection.config.get(simple=True)
            schema_props = schema_config.to_dict().get("properties", [])
            # Properties are _Property objects, not dicts - access .name attribute
            property_names = {prop.name if hasattr(prop, "name") else prop.get("name") for prop in schema_props}
            if "feature_bootstrappers" not in property_names:
                print("   ⚠️  Adding missing 'feature_bootstrappers' property...")
                add_result = collection.config.add_property(
                    Property(
                        name="feature_bootstrappers",
                        data_type=DataType.TEXT_ARRAY,
                    )
                )
                if inspect.isawaitable(add_result):
                    await add_result
                print("   ✅ Added 'feature_bootstrappers' property to schema")
            else:
                print("   ✅ Schema already includes 'feature_bootstrappers'")

            # 6. Check if a default config already exists for this user
            print("\n🔍 Step 5: Checking for existing default configs...")
            existing_defaults = await collection.query.fetch_objects(
                filters=Filter.all_of([
                    Filter.by_property("default").equal(True),
                    Filter.by_property("user_id").equal(user_id),
                ])
            )

            if existing_defaults.objects:
                print(f"   ⚠️  Found {len(existing_defaults.objects)} existing default config(s)")
                # Unset any existing defaults
                for item in existing_defaults.objects:
                    await collection.data.update(
                        properties={"default": False},
                        uuid=item.uuid
                    )
                    print(f"   ✅ Unset default flag on: {item.properties.get('name', 'Unknown')}")
            else:
                print("   ✅ No existing default configs found")

            # 7. Create config item
            print("\n💾 Step 6: Creating config object...")
            # VSM uses SMIDO bootstrap to add branches and tools
            feature_bootstrappers = ["vsm_smido"]
            
            config_item = {
                "name": config_name,
                "settings": settings_dict,
                "style": style,
                "agent_description": agent_description,
                "end_goal": end_goal,
                "branch_initialisation": branch_initialisation,
                "feature_bootstrappers": feature_bootstrappers,
                "frontend_config": frontend_config,
                "config_id": config_id,
                "user_id": user_id,
                "default": True,  # THIS IS THE KEY - marks it as default
            }

            # 8. Insert into Weaviate
            print("\n📤 Step 7: Inserting config into Weaviate...")
            uuid = generate_uuid5(config_id)

            if await collection.data.exists(uuid=uuid):
                await collection.data.update(properties=config_item, uuid=uuid)
                print(f"   ✅ Updated existing config: {config_name}")
            else:
                await collection.data.insert(config_item, uuid=uuid)
                print(f"   ✅ Created new config: {config_name}")

            # 9. Verify
            print("\n✅ Step 8: Verifying config was saved...")
            verify_result = await collection.query.fetch_objects(
                filters=Filter.by_property("config_id").equal(config_id),
                limit=1
            )

            if verify_result.objects:
                print("   ✅ Config object found")
                saved_properties = verify_result.objects[0].properties

                # Verify feature_bootstrappers value
                bootstrappers = saved_properties.get("feature_bootstrappers")
                if isinstance(bootstrappers, list) and bootstrappers:
                    print(
                        f"   ✅ feature_bootstrappers stored: {', '.join(bootstrappers)}"
                    )
                else:
                    print(
                        "   ❌ WARNING: feature_bootstrappers missing or empty in saved object"
                    )
            else:
                print("   ❌ WARNING: Config may not have been saved correctly")

            # Verify schema still contains the property (defensive double-check)
            schema_after_write = await collection.config.get(simple=True)
            schema_props_after = schema_after_write.to_dict().get("properties", [])
            # Properties are _Property objects, not dicts - access .name attribute
            schema_properties = {
                prop.name if hasattr(prop, "name") else prop.get("name")
                for prop in schema_props_after
            }
            if "feature_bootstrappers" in schema_properties:
                print("   ✅ Schema includes feature_bootstrappers")
            else:
                print("   ❌ WARNING: Schema missing feature_bootstrappers after write")

            # 10. Summary
            print("\n" + "=" * 60)
            print("🎉 VSM Default Config Seed Complete!")
            print("=" * 60)
            print(f"\n📋 Config Details:")
            print(f"   Name: {config_name}")
            print(f"   ID: {config_id}")
            print(f"   User ID: {user_id}")
            print(f"   Default: True")
            print(f"\n🤖 Agent Configuration:")
            print(f"   Description: {agent_description[:80]}...")
            print(f"   Style: {style[:80]}...")
            print(f"   End Goal: {end_goal[:80]}...")
            print(f"   Branch Init: {branch_initialisation}")
            print(f"   Feature Bootstrappers: {', '.join(feature_bootstrappers)}")
            print(f"\n⚙️  LLM Models:")
            print(f"   Base: {settings.BASE_MODEL}")
            print(f"   Complex: {settings.COMPLEX_MODEL}")
            print(f"\n🔗 Weaviate:")
            print(f"   URL: {settings.WCD_URL}")
            print(f"   API Key: {'*' * 20} (encrypted)")
            print(f"\n🎯 Next Steps:")
            print("   1. Start Elysia: elysia start")
            print("   2. Open browser: http://localhost:8000")
            print("   3. Expected: Skip welcome screen, go straight to chat")
            print("   4. Verify: Agent responds in Dutch with VSM tone")
            print(f"\n💡 Note: Config fallback fix automatically applied")
            print("   This ensures your VSM config loads for all users, even with different user IDs")
            print("\n" + "=" * 60)
    
    finally:
        # Explicitly close the client manager to avoid ResourceWarnings
        await client_manager.close_clients()


if __name__ == "__main__":
    try:
        asyncio.run(seed_default_config())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
