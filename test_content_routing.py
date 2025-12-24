#!/usr/bin/env python3
"""Test script for content routing system."""

import asyncio
import sys
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, '/home/bean12/Desktop/AI Service')

from app.services.content_classifier import get_content_classifier, ContentLabel
from app.services.content_router import get_content_router, ModelRoute
from app.services.session_manager import get_session_manager
from app.services.content_audit_logger import get_audit_logger


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_result(test_name: str, passed: bool, details: str = ""):
    """Print test result."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {test_name}")
    if details:
        print(f"     {details}")


def test_normalization():
    """Test text normalization."""
    print_header("Testing Normalization")
    
    classifier = get_content_classifier()
    
    test_cases = [
        ("s3x", "sex", "Leetspeak"),
        ("p0rn", "porn", "Leetspeak"),
        ("s e x", "sex", "Spacing trick"),
        ("🍆💦", "penis cum", "Emoji mapping"),
    ]
    
    for original, expected_word, test_type in test_cases:
        normalized = classifier._normalize_text(original)
        passed = expected_word in normalized
        print_result(
            f"{test_type}: '{original}' → '{normalized}'",
            passed,
            f"Expected '{expected_word}' in result"
        )


def test_classification():
    """Test content classification."""
    print_header("Testing Classification")
    
    classifier = get_content_classifier()
    
    test_cases = [
        ("How do I learn Python?", ContentLabel.SAFE, "Safe content"),
        ("You're so charming and attractive", ContentLabel.SUGGESTIVE, "Suggestive content"),
        ("I want to have sex with you", ContentLabel.EXPLICIT_CONSENSUAL_ADULT, "Explicit content"),
        ("I'm interested in BDSM roleplay", ContentLabel.EXPLICIT_FETISH, "Fetish content"),
        ("Let's roleplay a forced scenario", ContentLabel.NONCONSENSUAL, "Non-consensual"),
        ("Let's roleplay as teenagers", ContentLabel.MINOR_RISK, "Minor risk"),
        ("I have a medical question about anatomy", ContentLabel.SAFE, "Clinical context"),
    ]
    
    for text, expected_label, description in test_cases:
        result = classifier.classify(text)
        passed = result.label == expected_label
        
        print_result(
            description,
            passed,
            f"Got {result.label.value} (confidence: {result.confidence:.2f}), "
            f"expected {expected_label.value}"
        )
        
        if result.indicators:
            print(f"     Indicators: {', '.join(result.indicators[:3])}")


def test_routing():
    """Test content routing."""
    print_header("Testing Routing")
    
    classifier = get_content_classifier()
    router = get_content_router()
    
    test_cases = [
        (ContentLabel.SAFE, ModelRoute.NORMAL, "Safe → Normal"),
        (ContentLabel.SUGGESTIVE, ModelRoute.ROMANCE, "Suggestive → Romance"),
        (ContentLabel.EXPLICIT_CONSENSUAL_ADULT, ModelRoute.EXPLICIT, "Explicit → Explicit"),
        (ContentLabel.EXPLICIT_FETISH, ModelRoute.FETISH, "Fetish → Fetish"),
        (ContentLabel.NONCONSENSUAL, ModelRoute.REFUSAL, "Non-consensual → Refusal"),
        (ContentLabel.MINOR_RISK, ModelRoute.HARD_REFUSAL, "Minor risk → Hard refusal"),
    ]
    
    for label, expected_route, description in test_cases:
        # Create mock classification result
        from app.services.content_classifier import ClassificationResult
        classification = ClassificationResult(
            label=label,
            confidence=0.9,
            indicators=[],
            normalized_text="test",
            layer_results={}
        )
        
        route = router.route(classification)
        passed = route == expected_route
        
        print_result(
            description,
            passed,
            f"Got {route.value}, expected {expected_route.value}"
        )


def test_session_management():
    """Test session management."""
    print_header("Testing Session Management")
    
    session_manager = get_session_manager()
    
    # Create test conversation
    conversation_id = uuid4()
    user_id = uuid4()
    
    # Test 1: Initial state
    session = session_manager.get_session(conversation_id, user_id)
    passed = not session.age_verified
    print_result(
        "Initial state - age not verified",
        passed,
        f"age_verified = {session.age_verified}"
    )
    
    # Test 2: Age verification
    session_manager.verify_age(conversation_id)
    passed = session_manager.is_age_verified(conversation_id)
    print_result(
        "Age verification",
        passed,
        f"age_verified = {session_manager.is_age_verified(conversation_id)}"
    )
    
    # Test 3: Route lock-in
    session_manager.set_route(conversation_id, ModelRoute.EXPLICIT)
    passed = session_manager.is_route_locked(conversation_id)
    print_result(
        "Route lock-in for explicit content",
        passed,
        f"route_locked = {session_manager.is_route_locked(conversation_id)}, "
        f"lock_count = {session.route_lock_message_count}"
    )
    
    # Test 4: Requires age verification
    passed = not session_manager.requires_age_verification(conversation_id, ModelRoute.EXPLICIT)
    print_result(
        "Age verification not required (already verified)",
        passed
    )
    
    # Test 5: Clear session
    session_manager.clear_session(conversation_id)
    passed = conversation_id not in session_manager.sessions
    print_result(
        "Session cleared",
        passed
    )


def test_age_verification_flow():
    """Test age verification flow."""
    print_header("Testing Age Verification Flow")
    
    session_manager = get_session_manager()
    conversation_id = uuid4()
    user_id = uuid4()
    
    # Test 1: Explicit content without verification
    session = session_manager.get_session(conversation_id, user_id)
    requires_verification = session_manager.requires_age_verification(
        conversation_id, ModelRoute.EXPLICIT
    )
    passed = requires_verification
    print_result(
        "Explicit content requires age verification",
        passed
    )
    
    # Test 2: Track attempts
    attempt1 = session_manager.track_explicit_attempt(conversation_id)
    attempt2 = session_manager.track_explicit_attempt(conversation_id)
    passed = attempt1 == 1 and attempt2 == 2
    print_result(
        "Track explicit attempts",
        passed,
        f"Attempts: {attempt1}, {attempt2}"
    )
    
    # Test 3: Get verification prompt
    prompt = session_manager.get_age_verification_prompt(attempt1)
    passed = "18" in prompt and "age" in prompt.lower()
    print_result(
        "Age verification prompt generated",
        passed
    )
    
    # Test 4: Verify age
    session_manager.verify_age(conversation_id)
    requires_verification = session_manager.requires_age_verification(
        conversation_id, ModelRoute.EXPLICIT
    )
    passed = not requires_verification
    print_result(
        "Age verified - no longer required",
        passed
    )


def test_refusal_handling():
    """Test refusal handling."""
    print_header("Testing Refusal Handling")
    
    router = get_content_router()
    
    test_cases = [
        (ModelRoute.REFUSAL, "Non-consensual refusal"),
        (ModelRoute.HARD_REFUSAL, "Minor risk hard refusal"),
    ]
    
    for route, description in test_cases:
        should_refuse = router.should_refuse(route)
        refusal_message = router.get_refusal_message(route)
        
        passed = should_refuse and len(refusal_message) > 0
        print_result(
            description,
            passed,
            f"Refusal message: {refusal_message[:50]}..."
        )


def test_audit_logging():
    """Test audit logging."""
    print_header("Testing Audit Logging")
    
    from app.services.content_classifier import ClassificationResult
    
    audit_logger = get_audit_logger()
    conversation_id = uuid4()
    user_id = uuid4()
    
    # Create test classification
    classification = ClassificationResult(
        label=ContentLabel.EXPLICIT_CONSENSUAL_ADULT,
        confidence=0.85,
        indicators=["anatomy: penis", "sexual_act: sex"],
        normalized_text="normalized test",
        layer_results={"scores": {"anatomy": 2, "sexual_acts": 1}}
    )
    
    # Log classification
    audit_logger.log_classification(
        conversation_id=conversation_id,
        user_id=user_id,
        original_text="test message",
        classification=classification,
        route=ModelRoute.EXPLICIT,
        route_locked=True,
        age_verified=True,
        action="generate"
    )
    
    # Get stats
    stats = audit_logger.get_stats()
    
    passed = "total_logs" in stats
    print_result(
        "Audit logging and statistics",
        passed,
        f"Total logs: {stats.get('total_logs', 0)}"
    )


def test_system_prompts():
    """Test system prompts."""
    print_header("Testing System Prompts")
    
    router = get_content_router()
    
    routes = [
        ModelRoute.NORMAL,
        ModelRoute.ROMANCE,
        ModelRoute.EXPLICIT,
        ModelRoute.FETISH,
        ModelRoute.REFUSAL,
        ModelRoute.HARD_REFUSAL,
    ]
    
    for route in routes:
        prompt = router.get_system_prompt(route)
        passed = len(prompt) > 0
        
        print_result(
            f"{route.value} system prompt",
            passed,
            f"Length: {len(prompt)} chars"
        )


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("  CONTENT ROUTING SYSTEM - TEST SUITE")
    print("=" * 70)
    
    try:
        test_normalization()
        test_classification()
        test_routing()
        test_session_management()
        test_age_verification_flow()
        test_refusal_handling()
        test_audit_logging()
        test_system_prompts()
        
        print("\n" + "=" * 70)
        print("  TEST SUITE COMPLETE")
        print("=" * 70)
        print("\n✅ All tests completed. Review results above.\n")
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()

