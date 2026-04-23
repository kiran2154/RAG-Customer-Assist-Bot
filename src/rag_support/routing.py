from __future__ import annotations

from typing import Tuple


SENSITIVE_KEYWORDS = {
    "legal",
    "lawsuit",
    "fraud",
    "harassment",
    "threat",
    "regulator",
}

HUMAN_REQUEST_KEYWORDS = {
    "human",
    "agent",
    "representative",
    "manager",
    "complaint",
    "escalate",
}

BILLING_KEYWORDS = {"refund", "billing", "invoice", "charged", "chargeback"}
TECHNICAL_KEYWORDS = {"error", "bug", "issue", "crash", "login", "password"}

COMPLEXITY_MARKERS = {
    "timeline",
    "root cause",
    "compare",
    "exception",
    "multi-step",
    "policy exception",
}


def detect_intent(query: str) -> str:
    lower_query = query.lower()

    if any(keyword in lower_query for keyword in SENSITIVE_KEYWORDS):
        return "sensitive"

    if any(keyword in lower_query for keyword in HUMAN_REQUEST_KEYWORDS):
        return "human_request"

    if any(keyword in lower_query for keyword in BILLING_KEYWORDS):
        return "billing"

    if any(keyword in lower_query for keyword in TECHNICAL_KEYWORDS):
        return "technical"

    return "general"


def is_complex_query(query: str) -> bool:
    lower_query = query.lower()
    word_count = len(query.split())
    question_count = query.count("?")
    marker_found = any(marker in lower_query for marker in COMPLEXITY_MARKERS)

    return word_count > 55 or question_count > 1 or marker_found


def decide_route(
    *,
    query: str,
    intent: str,
    has_context: bool,
    top_score: float,
    confidence_threshold: float,
) -> Tuple[str, str]:
    reasons: list[str] = []

    if intent in {"sensitive", "human_request"}:
        reasons.append(f"intent={intent}")

    if not has_context:
        reasons.append("no_relevant_chunks")

    if top_score < confidence_threshold:
        reasons.append(f"low_confidence={top_score:.2f}")

    if is_complex_query(query):
        reasons.append("complex_query")

    if reasons:
        return "escalate", "; ".join(reasons)

    return "auto_answer", "sufficient_context"
