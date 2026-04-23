from __future__ import annotations

from pathlib import Path
import sys

import streamlit as st


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rag_support.config import Settings  # noqa: E402
from rag_support.ingest import ingest_pdf  # noqa: E402
from rag_support.retrieval import KnowledgeRetriever  # noqa: E402
from rag_support.workflow import SupportAssistant  # noqa: E402


def _is_streamlit_runtime() -> bool:
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
    except Exception:
        return False

    return get_script_run_ctx() is not None


@st.cache_resource(show_spinner="Loading embedding model and vector index...")
def get_retriever() -> KnowledgeRetriever:
    settings = Settings.from_env(ROOT)
    return KnowledgeRetriever(settings)


def run_query(query: str, human_reply: str) -> dict:
    settings = Settings.from_env(ROOT)
    retriever = get_retriever()

    def web_human_responder(_query: str, reason: str) -> str:
        reply = human_reply.strip()
        if reply:
            return reply
        return (
            "Escalation pending. No human response was provided in the sidebar. "
            f"Reason: {reason}"
        )

    assistant = SupportAssistant(
        settings=settings,
        retriever=retriever,
        human_responder=web_human_responder,
    )
    return assistant.run(query)


def init_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []


def ingest_from_sidebar() -> None:
    st.sidebar.subheader("Knowledge Base")
    uploaded_pdf = st.sidebar.file_uploader("Upload PDF", type=["pdf"])
    pdf_path_input = st.sidebar.text_input("Or use existing PDF path", value="data/customer_support_kb.pdf")
    reset_collection = st.sidebar.checkbox("Reset collection before ingest", value=True)

    if st.sidebar.button("Ingest PDF", use_container_width=True):
        settings = Settings.from_env(ROOT)
        try:
            if uploaded_pdf is not None:
                upload_dir = ROOT / "data" / "uploaded"
                upload_dir.mkdir(parents=True, exist_ok=True)
                pdf_path = upload_dir / uploaded_pdf.name
                pdf_path.write_bytes(uploaded_pdf.getvalue())
            else:
                pdf_path = Path(pdf_path_input)
                if not pdf_path.is_absolute():
                    pdf_path = ROOT / pdf_path

            pages, chunks = ingest_pdf(pdf_path, settings, reset_collection=reset_collection)
        except Exception as exc:
            st.sidebar.error(f"Ingestion failed: {exc}")
            return

        # Recreate cached retriever against the latest index.
        st.cache_resource.clear()
        st.sidebar.success(f"Ingested {pages} pages and stored {chunks} chunks.")


def render_chat(human_reply: str) -> None:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("meta"):
                st.caption(message["meta"])
            if message.get("sources"):
                st.caption("Sources: " + ", ".join(message["sources"]))

    query = st.chat_input("Ask a customer support question")
    if not query:
        return

    st.session_state.messages.append({"role": "user", "content": query})

    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Running LangGraph workflow..."):
            try:
                result = run_query(query, human_reply)
            except Exception as exc:
                error_text = f"Request failed: {exc}"
                st.error(error_text)
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": error_text,
                    }
                )
                return

        answer = result.get("answer", "No answer generated.")
        intent = result.get("intent", "unknown")
        route = result.get("route", "unknown")
        confidence = float(result.get("confidence", 0.0))
        reason = result.get("escalation_reason", "n/a")
        sources = result.get("sources", [])

        meta = (
            f"intent={intent} | route={route} | "
            f"confidence={confidence:.2f} | reason={reason}"
        )

        st.markdown(answer)
        st.caption(meta)
        if sources:
            st.caption("Sources: " + ", ".join(sources))

        with st.expander("Retrieved chunks"):
            chunks = result.get("retrieved_chunks", [])
            if not chunks:
                st.write("No chunks returned.")
            for chunk in chunks:
                page = chunk.get("page", "?")
                score = float(chunk.get("score", 0.0))
                content = str(chunk.get("content", ""))
                snippet = content[:350] + ("..." if len(content) > 350 else "")
                st.markdown(f"Page {page} | score={score:.2f}")
                st.write(snippet)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer,
                "meta": meta,
                "sources": sources,
            }
        )


def main() -> None:
    st.set_page_config(
        page_title="RAG Support Assistant",
        page_icon="🧭",
        layout="wide",
    )

    init_state()

    st.title("RAG Customer Support Assistant")
    st.caption("LangGraph workflow with retrieval, intent routing, and HITL escalation.")

    settings = Settings.from_env(ROOT)
    if not settings.groq_api_key:
        st.warning("GROQ_API_KEY is missing in .env. Auto-answer route will fail until configured.")

    ingest_from_sidebar()

    st.sidebar.subheader("HITL")
    human_reply = st.sidebar.text_area(
        "Human response used when escalation occurs",
        placeholder="Type a human agent response here for escalated queries...",
    )

    if st.sidebar.button("Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    render_chat(human_reply)


if __name__ == "__main__":
    if not _is_streamlit_runtime():
        print("This Streamlit app must be started with: streamlit run streamlit_app.py")
        raise SystemExit(0)

    main()
