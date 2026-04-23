from __future__ import annotations

from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config import Settings


def build_embeddings(settings: Settings) -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name=settings.embedding_model)


def ingest_pdf(pdf_path: Path, settings: Settings, reset_collection: bool = True) -> tuple[int, int]:
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    settings.ensure_directories()

    loader = PyPDFLoader(str(pdf_path))
    pages = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(pages)

    for index, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = index
        chunk.metadata["source_path"] = str(pdf_path)

    embeddings = build_embeddings(settings)

    if reset_collection:
        existing = Chroma(
            collection_name=settings.chroma_collection,
            persist_directory=str(settings.chroma_dir),
            embedding_function=embeddings,
        )
        try:
            existing.delete_collection()
        except Exception:
            pass

    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=settings.chroma_collection,
        persist_directory=str(settings.chroma_dir),
    )

    if hasattr(vector_store, "persist"):
        vector_store.persist()

    return len(pages), len(chunks)
