#!/usr/bin/env python3
"""
Test LLM models through Elysia Tree interface (proper provider routing)
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env file
from dotenv import load_dotenv
env_path = project_root / ".env"
load_dotenv(env_path)

print("="*80)
print("TESTING MODELS VIA ELYSIA TREE")
print("="*80)

print(f"\nConfiguration:")
print(f"  BASE_MODEL: {os.getenv('BASE_MODEL')}")
print(f"  BASE_PROVIDER: {os.getenv('BASE_PROVIDER')}")
print(f"  COMPLEX_MODEL: {os.getenv('COMPLEX_MODEL')}")
print(f"  COMPLEX_PROVIDER: {os.getenv('COMPLEX_PROVIDER')}")

print("\n" + "="*80)
print("TEST 1: Create Tree with Settings")
print("="*80)

try:
    from elysia import Tree, Settings

    settings = Settings.from_smart_setup()
    tree = Tree(
        branch_initialisation="empty",
        low_memory=False,  # Load models to test them
        settings=settings
    )

    print("✅ Tree created successfully with models loaded")
    print(f"   Tree has access to base_lm: {tree._base_lm is not None}")
    print(f"   Tree has access to complex_lm: {tree._complex_lm is not None}")

except Exception as e:
    print(f"❌ Failed to create tree: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*80)
print("TEST 2: Test Base Model via Tree")
print("="*80)

try:
    if tree._base_lm:
        response = tree._base_lm("Say 'BASE MODEL OK' in exactly three words.")
        print(f"✅ Base Model Response: {response}")
    else:
        print("❌ Base model not loaded")
except Exception as e:
    print(f"❌ Base model test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("TEST 3: Test Complex Model via Tree")
print("="*80)

try:
    if tree._complex_lm:
        response = tree._complex_lm("Say 'COMPLEX MODEL OK' in exactly three words.")
        print(f"✅ Complex Model Response: {response}")
    else:
        print("❌ Complex model not loaded")
except Exception as e:
    print(f"❌ Complex model test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print("If both models responded successfully, your configuration is correct!")
print("The model format you're using works with Elysia's Tree interface.")
