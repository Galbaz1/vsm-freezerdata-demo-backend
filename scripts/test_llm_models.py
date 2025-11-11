#!/usr/bin/env python3
"""
Quick test to verify base and complex LLM models are working with current .env settings.
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
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded .env from {env_path}")
else:
    print(f"⚠️  .env file not found at {env_path}")

def test_env_vars():
    """Check that required environment variables are set"""
    print("\n" + "="*80)
    print("ENVIRONMENT VARIABLES CHECK")
    print("="*80)

    required_vars = [
        'BASE_MODEL',
        'COMPLEX_MODEL',
        'OPENAI_API_KEY',
        'GOOGLE_API_KEY',
        'WCD_URL',
        'WCD_API_KEY'
    ]

    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'KEY' in var or 'API' in var:
                display_value = f"{value[:8]}..." if len(value) > 8 else "***"
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: NOT SET")
            missing.append(var)

    if missing:
        print(f"\n❌ Missing environment variables: {', '.join(missing)}")
        print("   Please check your .env file")
        return False

    print("\n✅ All required environment variables are set")
    return True


def test_base_model():
    """Test base model (typically GPT-4 for decision-making)"""
    print("\n" + "="*80)
    print("BASE MODEL TEST")
    print("="*80)

    try:
        base_model = os.getenv('BASE_MODEL')
        if not base_model:
            print("❌ BASE_MODEL not set in environment")
            return False

        print(f"Base Model: {base_model}")
        print("Testing model with simple query...")

        # Create a simple DSPy signature for testing
        import dspy

        # Configure DSPy with the base model
        lm = dspy.LM(base_model)

        # Simple test query
        response = lm("Say 'Hello from base model' in exactly 5 words.")

        print(f"✅ Base Model Response: {response}")
        print(f"✅ Base model ({base_model}) is working!")
        return True

    except Exception as e:
        print(f"❌ Base model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_complex_model():
    """Test complex model (typically Gemini for complex reasoning)"""
    print("\n" + "="*80)
    print("COMPLEX MODEL TEST")
    print("="*80)

    try:
        complex_model = os.getenv('COMPLEX_MODEL')
        if not complex_model:
            print("❌ COMPLEX_MODEL not set in environment")
            return False

        print(f"Complex Model: {complex_model}")
        print("Testing model with simple query...")

        # Create a simple DSPy signature for testing
        import dspy

        # Configure DSPy with the complex model
        lm = dspy.LM(complex_model)

        # Simple test query
        response = lm("Say 'Hello from complex model' in exactly 5 words.")

        print(f"✅ Complex Model Response: {response}")
        print(f"✅ Complex model ({complex_model}) is working!")
        return True

    except Exception as e:
        print(f"❌ Complex model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_elysia_settings():
    """Test that Elysia Settings can be loaded"""
    print("\n" + "="*80)
    print("ELYSIA SETTINGS TEST")
    print("="*80)

    try:
        from elysia import Settings

        settings = Settings.from_smart_setup()

        # Access settings via dictionary-like interface or attributes
        print(f"Settings type: {type(settings)}")
        print(f"Settings attributes: {dir(settings)[:10]}...")

        # Try to get model info from environment since Settings doesn't expose them directly
        base_model = os.getenv('BASE_MODEL', 'Not set')
        complex_model = os.getenv('COMPLEX_MODEL', 'Not set')

        print(f"Base Model (from env): {base_model}")
        print(f"Complex Model (from env): {complex_model}")

        print("\n✅ Elysia Settings loaded successfully!")
        return True

    except Exception as e:
        print(f"❌ Elysia Settings test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all LLM model tests"""
    print("\n" + "="*80)
    print("LLM MODELS VERIFICATION TEST")
    print("="*80)
    print("Testing that base and complex models work with current .env settings\n")

    results = []

    # Test 1: Environment variables
    results.append(("Environment Variables", test_env_vars()))

    # Test 2: Elysia Settings
    results.append(("Elysia Settings", test_elysia_settings()))

    # Test 3: Base Model
    results.append(("Base Model", test_base_model()))

    # Test 4: Complex Model
    results.append(("Complex Model", test_complex_model()))

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")

    total = len(results)
    passed = sum(1 for _, p in results if p)

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Your LLM models are configured correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check your .env configuration.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
