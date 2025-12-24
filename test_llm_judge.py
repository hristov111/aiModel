#!/usr/bin/env python3
"""Test script for LLM judge (Layer 4) functionality."""

import asyncio
import sys
sys.path.insert(0, '/home/bean12/Desktop/AI Service')

from app.services.content_classifier import ContentClassifier, ContentLabel
from app.services.llm_client import OpenAIClient
from app.core.config import settings


async def test_llm_judge():
    """Test LLM judge with borderline cases."""
    
    print("=" * 70)
    print("  LLM JUDGE TEST (Layer 4)")
    print("=" * 70)
    print()
    
    # Check if OpenAI API key is available
    if not settings.openai_api_key:
        print("❌ OPENAI_API_KEY not set. Cannot test LLM judge.")
        print("   Set OPENAI_API_KEY in .env to test Layer 4.")
        return
    
    print("✅ OpenAI API key found")
    print()
    
    # Create classifier with LLM judge
    llm_client = OpenAIClient(
        model_name="gpt-4o-mini",
        temperature=0.3,
        max_tokens=150
    )
    
    classifier = ContentClassifier(llm_client=llm_client, enable_llm_judge=True)
    
    print(f"Classifier initialized with LLM judge enabled")
    print(f"Confidence threshold: {classifier.LLM_CONFIDENCE_THRESHOLD}")
    print()
    
    # Test cases - borderline content that should trigger LLM judge
    test_cases = [
        {
            "text": "Let's get intimate tonight",
            "expected": ContentLabel.SUGGESTIVE,
            "description": "Borderline suggestive - ambiguous intent"
        },
        {
            "text": "You look really young for your age",
            "expected": ContentLabel.MINOR_RISK,
            "description": "Age ambiguity - LLM should catch this"
        },
        {
            "text": "I want to cuddle with you",
            "expected": ContentLabel.SAFE,  # LLM correctly identifies this as innocent
            "description": "Intimate but innocent (cuddling)"
        },
        {
            "text": "Tell me about your bedroom activities",
            "expected": ContentLabel.EXPLICIT_CONSENSUAL_ADULT,
            "description": "Indirect explicit reference"
        },
        {
            "text": "Let's explore our fantasies together",
            "expected": ContentLabel.SUGGESTIVE,
            "description": "Suggestive but vague"
        },
    ]
    
    print("=" * 70)
    print("  TESTING BORDERLINE CASES")
    print("=" * 70)
    print()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['description']}")
        print(f"Input: \"{test_case['text']}\"")
        
        result = classifier.classify(test_case['text'])
        
        print(f"Label: {result.label.value} (confidence: {result.confidence:.2f})")
        print(f"Expected: {test_case['expected'].value}")
        
        # Check if LLM judge was used
        used_llm = "llm_judge" in result.layer_results
        print(f"LLM Judge Used: {'✅ YES' if used_llm else '❌ NO'}")
        
        if used_llm:
            llm_result = result.layer_results.get("llm_judge", {})
            print(f"LLM Result: {llm_result.get('label', 'N/A')} "
                  f"(confidence: {llm_result.get('confidence', 0):.2f})")
            if "reasoning" in llm_result:
                print(f"LLM Reasoning: {llm_result['reasoning']}")
        
        # Show indicators
        if result.indicators:
            print(f"Indicators: {', '.join(result.indicators[:3])}")
        
        # Check if passed
        passed = result.label == test_case['expected']
        print(f"Result: {'✅ PASS' if passed else '❌ FAIL'}")
        print()
    
    print("=" * 70)
    print("  LLM JUDGE TEST COMPLETE")
    print("=" * 70)


async def test_llm_judge_caching():
    """Test LLM judge caching."""
    
    print()
    print("=" * 70)
    print("  TESTING LLM JUDGE CACHING")
    print("=" * 70)
    print()
    
    if not settings.openai_api_key:
        print("❌ Skipping cache test - no API key")
        return
    
    llm_client = OpenAIClient(model_name="gpt-4o-mini", temperature=0.3, max_tokens=150)
    classifier = ContentClassifier(llm_client=llm_client, enable_llm_judge=True)
    
    test_text = "Let's get intimate tonight"
    
    print(f"Test text: \"{test_text}\"")
    print()
    
    # First call - should hit LLM
    print("1st classification (should use LLM)...")
    import time
    start = time.time()
    result1 = classifier.classify(test_text)
    duration1 = time.time() - start
    print(f"   Duration: {duration1:.2f}s")
    print(f"   Label: {result1.label.value}")
    used_llm1 = "llm_judge" in result1.layer_results
    print(f"   LLM Used: {'✅ YES' if used_llm1 else '❌ NO'}")
    
    # Second call - should use cache
    print()
    print("2nd classification (should use cache)...")
    start = time.time()
    result2 = classifier.classify(test_text)
    duration2 = time.time() - start
    print(f"   Duration: {duration2:.2f}s")
    print(f"   Label: {result2.label.value}")
    used_llm2 = "llm_judge" in result2.layer_results
    print(f"   LLM Used: {'✅ YES' if used_llm2 else '❌ NO'}")
    
    print()
    if duration2 < duration1 * 0.5:  # Cache should be much faster
        print("✅ CACHE WORKING - 2nd call much faster")
    else:
        print("⚠️  CACHE MAY NOT BE WORKING - similar durations")
    
    print()


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  CONTENT CLASSIFICATION - LAYER 4 (LLM JUDGE) TEST")
    print("=" * 70)
    
    try:
        asyncio.run(test_llm_judge())
        asyncio.run(test_llm_judge_caching())
        
        print("\n✅ All LLM judge tests completed\n")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

