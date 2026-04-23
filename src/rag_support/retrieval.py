from __future__ import annotations

from dataclasses import dataclass

from langchain_chroma import Chroma

from .config import Settings
from .ingest import build_embeddings
from .schemas import RetrievedChunk


@dataclass
class RetrievalResult:
    chunks: list[RetrievedChunk]
    context: str
    top_score: float


class KnowledgeRetriever:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._vector_store = Chroma(
            collection_name=settings.chroma_collection,
            persist_directory=str(settings.chroma_dir),
            embedding_function=build_embeddings(settings),
        )

    @staticmethod
    def _distance_to_confidence(distance: float) -> float:
        numeric_distance = float(distance)

        # Defensive fallback for backend edge cases.
        if numeric_distance != numeric_distance:
            return 0.0

        if numeric_distance < 0.0:
            numeric_distance = 0.0

        confidence = 1.0 / (1.0 + numeric_distance)
        return max(0.0, min(1.0, confidence))

    def retrieve(self, query: str) -> RetrievalResult:
        docs_with_distances = self._vector_store.similarity_search_with_score(
            query,
            k=self.settings.top_k,
        )

        chunks: list[RetrievedChunk] = []
        context_parts: list[str] = []
        top_score = 0.0

        for doc, distance in docs_with_distances:
            score = self._distance_to_confidence(distance)
            top_score = max(top_score, score)
            metadata = doc.metadata or {}
            chunk: RetrievedChunk = {
                "chunk_id": str(metadata.get("chunk_index", "unknown")),
                "page": int(metadata.get("page", -1)),
                "score": score,
                "content": doc.page_content,
            }
            chunks.append(chunk)
            context_parts.append(doc.page_content)

        return RetrievalResult(
            chunks=chunks,
            context="\n\n".join(context_parts),
            top_score=top_score,
        )
