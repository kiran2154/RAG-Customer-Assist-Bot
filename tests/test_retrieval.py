from rag_support.retrieval import KnowledgeRetriever


def test_distance_to_confidence_bounds() -> None:
    assert KnowledgeRetriever._distance_to_confidence(0.0) == 1.0
    assert KnowledgeRetriever._distance_to_confidence(1.0) == 0.5


def test_distance_to_confidence_negative_distance() -> None:
    assert KnowledgeRetriever._distance_to_confidence(-0.2) == 1.0


def test_distance_to_confidence_large_distance() -> None:
    score = KnowledgeRetriever._distance_to_confidence(99.0)
    assert 0.0 <= score <= 1.0
    assert score < 0.02


def test_distance_to_confidence_nan() -> None:
    assert KnowledgeRetriever._distance_to_confidence(float("nan")) == 0.0
