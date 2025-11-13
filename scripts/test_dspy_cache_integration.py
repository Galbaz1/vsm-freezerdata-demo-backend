"""
Test DSPy cache integration - verify if cached_content can be passed to DSPy LM.
"""
import asyncio
import os
import dspy
from elysia import configure
from features.vsm_tree.smido_tree import create_vsm_tree

async def test_dspy_cache():
    """Test if DSPy LM can use cached_content."""
    print("\n" + "="*70)
    print("Testing DSPy Cache Integration")
    print("="*70 + "\n")
    
    # Configure Elysia
    configure(
        base_model="gemini-2.5-flash",
        base_provider="gemini",
        complex_model="gemini-2.5-pro",
        complex_provider="gemini",
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    
    # Create tree (creates cache)
    print("1. Creating VSM tree (creates Gemini cache)...")
    tree = create_vsm_tree()
    
    cache_name = None
    if hasattr(tree, '_context_cache') and tree._context_cache.get_cache_name():
        cache_name = tree._context_cache.get_cache_name()
        print(f"   ✅ Cache created: {cache_name}")
    else:
        print("   ❌ Cache not created")
        return False
    
    # Check DSPy LM configuration
    print("\n2. Checking DSPy LM configuration...")
    base_lm = tree.base_lm
    print(f"   Base LM: {base_lm}")
    print(f"   Base LM model: {getattr(base_lm, 'model', 'N/A')}")
    print(f"   Base LM kwargs: {getattr(base_lm, 'kwargs', {})}")
    
    # Try to pass cached_content via extra kwargs
    print("\n3. Testing if cached_content can be passed via extra kwargs...")
    
    # Create a simple DSPy module
    class SimpleModule(dspy.Module):
        def __init__(self):
            super().__init__()
            self.predict = dspy.Predict("question -> answer")
        
        def forward(self, question, lm=None, **kwargs):
            return self.predict(question=question, lm=lm, **kwargs)
    
    module = SimpleModule()
    
    # Test 1: Without cache
    print("\n   Test 1: Without cached_content")
    try:
        result1 = module("What is SMIDO?", lm=base_lm)
        print(f"   ✅ Result: {result1.answer[:50]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: With cached_content in kwargs (if DSPy supports it)
    print("\n   Test 2: With cached_content in kwargs")
    try:
        result2 = module("What is SMIDO?", lm=base_lm, cached_content=cache_name)
        print(f"   ✅ Result: {result2.answer[:50]}...")
        print("   ⚠️  Note: This doesn't prove cache is used, need to check usage_metadata")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print("   → DSPy LM may not accept cached_content directly")
    
    # Test 3: Check if we can monkey-patch LM
    print("\n   Test 3: Checking LM internals...")
    print(f"   LM type: {type(base_lm)}")
    print(f"   LM dir: {[x for x in dir(base_lm) if not x.startswith('_')][:10]}")
    
    # Check if LM has a way to pass extra config
    if hasattr(base_lm, 'model'):
        print(f"   LM model attribute: {base_lm.model}")
    
    if hasattr(base_lm, 'kwargs'):
        print(f"   LM kwargs: {base_lm.kwargs}")
        # Try adding cached_content to kwargs
        if isinstance(base_lm.kwargs, dict):
            base_lm.kwargs['cached_content'] = cache_name
            print(f"   ✅ Added cached_content to LM kwargs: {base_lm.kwargs}")
    
    print("\n" + "="*70)
    print("Conclusion:")
    print("="*70)
    print("DSPy LM may need custom wrapper or monkey-patching to support cached_content.")
    print("Next step: Create custom LM wrapper that injects cached_content into API calls.")
    print("="*70 + "\n")
    
    return True

if __name__ == "__main__":
    if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
        print("WARNING: GOOGLE_API_KEY not set")
    
    asyncio.run(test_dspy_cache())

