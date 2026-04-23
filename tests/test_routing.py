from rag_support.routing import decide_route, detect_intent, is_complex_query


def test_detect_intent_sensitive() -> None:
    assert detect_intent("I will file a legal complaint") == "sensitive"


def test_detect_intent_billing() -> None:
    assert detect_intent("I need a refund for a wrong charge") == "billing"


def test_complex_query_detection() -> None:
    query = "Can you compare policy options and provide a timeline for each path?"
    assert is_complex_query(query) is True


def test_route_escalates_for_low_confidence() -> None:
    route, reason = decide_route(
        query="Normal help question",
        intent="general",
        has_context=True,
        top_score=0.1,
        confidence_threshold=0.35,
    )
    assert route == "escalate"
    assert "low_confidence" in reason


def test_route_auto_answer_when_confident() -> None:
    route, reason = decide_route(
        query="How do I reset password?",
        intent="technical",
        has_context=True,
        top_score=0.78,
        confidence_threshold=0.35,
    )
    assert route == "auto_answer"
    assert reason == "sufficient_context"
