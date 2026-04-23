from __future__ import annotations

from typing import Literal, TypedDict


RouteType = Literal["auto_answer", "escalate"]


class RetrievedChunk(TypedDict):
    chunk_id: str
    page: int
    score: float
    content: str


class SupportState(TypedDict, total=False):
    query: str
    intent: str
    route: RouteType
    escalation_reason: str
    confidence: float
    retrieved_chunks: list[RetrievedChunk]
    context: str
    answer: str
    sources: list[str]
    human_response: str
