#!/usr/bin/env python3
"""Quick test to verify both base and complex models work via Elysia Tree"""

from dotenv import load_dotenv
load_dotenv()

import asyncio
import os
from elysia import Tree, tool
from elysia.config import Settings, load_base_lm, load_complex_lm
import dspy

print("\n" + "="*80)
print("QUICK MODEL TEST - Testing Both Base and Complex Models")
print("="*80)

print(f"\nConfiguration:")
print(f"  BASE_MODEL: {os.getenv('BASE_MODEL')}")
print(f"  COMPLEX_MODEL: {os.getenv('COMPLEX_MODEL')}")
print(f"  BASE_PROVIDER: {os.getenv('BASE_PROVIDER')}")
print(f"  COMPLEX_PROVIDER: {os.getenv('COMPLEX_PROVIDER')}")

# Load settings
settings = Settings()
settings.set_from_env()

print("\n" + "="*80)
print("TEST 1: Base Model (Decision Agent)")
print("="*80)

try:
    # Test base model directly
    print("\n🔍 Loading base model...")
    base_lm = load_base_lm(settings)
    print(f"✅ Base model loaded: {settings.BASE_PROVIDER}/{settings.BASE_MODEL}")

    # Set as default for DSPy
    dspy.configure(lm=base_lm)

    # Create a simple signature
    class SimpleQA(dspy.Signature):
        """Answer questions concisely"""
        question = dspy.InputField()
        answer = dspy.OutputField()

    # Test it
    print("🔍 Testing base model with simple query...")
    predictor = dspy.Predict(SimpleQA)
    result = predictor(question="Respond with exactly 5 words about AI.")
    print(f"✅ BASE MODEL RESPONSE: {result.answer}")

except Exception as e:
    print(f"\n❌ Base model test failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "="*80)
print("TEST 2: Complex Model (Query Agent)")
print("="*80)

try:
    # Test complex model directly
    print("\n🔍 Loading complex model...")
    complex_lm = load_complex_lm(settings)
    print(f"✅ Complex model loaded: {settings.COMPLEX_PROVIDER}/{settings.COMPLEX_MODEL}")

    # Set as default for DSPy
    dspy.configure(lm=complex_lm)

    # Create a signature for semantic search
    class SemanticAnalysis(dspy.Signature):
        """Analyze text semantically"""
        text = dspy.InputField()
        summary = dspy.OutputField()

    # Test it
    print("🔍 Testing complex model with semantic query...")
    predictor = dspy.Predict(SemanticAnalysis)
    result = predictor(text="De verdamper is ingevroren door een defecte ontdooicyclus.")
    print(f"✅ COMPLEX MODEL RESPONSE: {result.summary}")

except Exception as e:
    print(f"\n❌ Complex model test failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "="*80)
print("TEST 3: Integration Test via Elysia Tree")
print("="*80)

try:
    # Create simple tool to test with
    @tool()
    async def simple_test():
        """Test tool that returns a message"""
        yield "This is a test tool response"

    # Create tree
    print("\n🔍 Creating Elysia tree...")
    tree = Tree(branch_initialisation='empty')
    tree.add_branch('test', 'Test branch', root=True)
    tree.add_tool(simple_test, 'test')

    # Test with query that will use base model (decision agent)
    print("🔍 Testing tree execution (uses base model for decisions)...")
    response = tree('Respond with exactly 3 words.')
    print(f"✅ TREE RESPONSE: {response[0][:100]}...")

except Exception as e:
    print(f"\n❌ Tree test failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "="*80)
print("RESULT: All Models Working Correctly!")
print("="*80)
print("\n✅ Base model (gpt-4.1) via OpenAI: WORKING")
print("✅ Complex model (gemini/gemini-2.5-pro) via Google: WORKING")
print("✅ Elysia Tree integration: WORKING")
print("\n" + "="*80)
