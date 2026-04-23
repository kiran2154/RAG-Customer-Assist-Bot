from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    groq_api_key: str
    groq_model: str
    embedding_model: str
    chroma_dir: Path
    chroma_collection: str
    chunk_size: int
    chunk_overlap: int
    top_k: int
    confidence_threshold: float

    @classmethod
    def from_env(cls, base_dir: Path | None = None) -> "Settings":
        root = base_dir or Path.cwd()
        chroma_dir = root / os.getenv("CHROMA_DIR", "chroma_db")
        return cls(
            groq_api_key=os.getenv("GROQ_API_KEY", ""),
            groq_model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
            embedding_model=os.getenv(
                "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
            ),
            chroma_dir=chroma_dir,
            chroma_collection=os.getenv("CHROMA_COLLECTION", "customer_support_kb"),
            chunk_size=int(os.getenv("CHUNK_SIZE", "900")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "150")),
            top_k=int(os.getenv("TOP_K", "4")),
            confidence_threshold=float(os.getenv("CONFIDENCE_THRESHOLD", "0.35")),
        )

    def ensure_directories(self) -> None:
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
