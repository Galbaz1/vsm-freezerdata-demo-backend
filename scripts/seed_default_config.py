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


async def seed_default_config():
    """Create a default config in ELYSIA_CONFIG__ collection."""

    print("🔧 VSM Default Config Seed Script")
    print("=" * 60)

    # 1. Extract VSM prompts from smido_tree.py
    print("\n📝 Step 1: Extracting VSM prompts from smido_tree.py...")
    from features.vsm_tree.smido_tree import create_vsm_tree

    # Create temporary VSM tree to extract its configuration
    temp_tree = create_vsm_tree(with_orchestrator=False)

    # Extract from tree_data.atlas (where Tree stores these values)
    agent_description = temp_tree.tree_data.atlas.agent_description
    style = temp_tree.tree_data.atlas.style
    end_goal = temp_tree.tree_data.atlas.end_goal
    suggestions_context = temp_tree.tree_data.atlas.suggestions_context
    branch_initialisation = "empty"  # VSM uses empty init

    print(f"   ✅ Agent Description: {len(agent_description)} characters")
    print(f"   ✅ Style: {len(style)} characters")
    print(f"   ✅ End Goal: {len(end_goal)} characters")
    print(f"   ✅ Suggestions Context: {len(suggestions_context)} characters")
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
                        Property(name="suggestions_context", data_type=DataType.TEXT),
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

            # Ensure feature_bootstrappers and suggestions_context properties exist (for existing collections)
            print("\n🛠️  Step 5a: Ensuring schema includes all required properties...")
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
            
            if "suggestions_context" not in property_names:
                print("   ⚠️  Adding missing 'suggestions_context' property...")
                add_result = collection.config.add_property(
                    Property(
                        name="suggestions_context",
                        data_type=DataType.TEXT,
                    )
                )
                if inspect.isawaitable(add_result):
                    await add_result
                print("   ✅ Added 'suggestions_context' property to schema")
            else:
                print("   ✅ Schema already includes 'suggestions_context'")

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
                "suggestions_context": suggestions_context,
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

            # Verify schema still contains the properties (defensive double-check)
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
            
            if "suggestions_context" in schema_properties:
                print("   ✅ Schema includes suggestions_context")
            else:
                print("   ❌ WARNING: Schema missing suggestions_context after write")

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
            print(f"   Suggestions Context: {suggestions_context[:80]}...")
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
