from __future__ import annotations

from pathlib import Path
import sys
import time

import streamlit as st

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rag_support.config import Settings
from rag_support.ingest import ingest_pdf
from rag_support.retrieval import KnowledgeRetriever
from rag_support.workflow import SupportAssistant

def _is_streamlit_runtime() -> bool:
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
    except Exception:
        return False

    return get_script_run_ctx() is not None


@st.cache_resource(show_spinner="Loading vector database...")
def get_retriever() -> KnowledgeRetriever:
    settings = Settings.from_env(ROOT)
    return KnowledgeRetriever(settings)


# ================================
# RUN QUERY
# ================================

def run_query(query: str, human_reply: str) -> dict:

    settings = Settings.from_env(ROOT)
    retriever = get_retriever()

    def web_human_responder(_query: str, reason: str) -> str:

        reply = human_reply.strip()

        if reply:
            return reply

        return f"Escalation pending. Reason: {reason}"

    assistant = SupportAssistant(
        settings=settings,
        retriever=retriever,
        human_responder=web_human_responder,
    )

    return assistant.run(query)


# ================================
# SESSION STATE
# ================================

def init_state():

    if "messages" not in st.session_state:
        st.session_state.messages = []


# ================================
# PREMIUM CSS
# ================================

def inject_custom_css():

    st.markdown("""
    <style>

    /* MAIN BACKGROUND */

    .main {
        background:
        radial-gradient(circle at top left, #1e293b, #020617);
        color: white;
    }

    .block-container {
        padding-top: 2rem;
        max-width: 1400px;
    }

    /* TITLE */

    .main-title {
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(to right, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }

    .subtitle {
        color: #94a3b8;
        margin-bottom: 2rem;
    }

    /* SIDEBAR */

    [data-testid="stSidebar"] {
        background: rgba(15,23,42,0.85);
        backdrop-filter: blur(12px);
        border-right: 1px solid rgba(255,255,255,0.08);
    }

    /* BUTTONS */

    .stButton button {
        border-radius: 14px;
        border: none;
        background:
        linear-gradient(to right, #2563eb, #7c3aed);

        color: white;
        font-weight: 600;
        padding: 0.7rem 1rem;

        transition: 0.3s ease;
    }

    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 0 20px rgba(99,102,241,0.4);
    }

    /* INPUTS */

    .stTextInput input,
    .stTextArea textarea {
        border-radius: 14px !important;
        background-color: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        color: white;
    }

    /* CHAT */

    .stChatMessage {
        background: rgba(255,255,255,0.03);
        backdrop-filter: blur(14px);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 18px;
        padding: 14px;
        margin-bottom: 14px;
    }

    /* METRIC CARDS */

    [data-testid="metric-container"] {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.06);
        padding: 1rem;
        border-radius: 16px;
        backdrop-filter: blur(12px);
    }

    /* EXPANDER */

    .streamlit-expanderHeader {
        font-size: 1rem;
        font-weight: 600;
    }

    /* STATUS BADGES */

    .badge {
        padding: 0.35rem 0.7rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin-right: 0.5rem;
    }

    .badge-tech {
        background: rgba(59,130,246,0.15);
        color: #60a5fa;
    }

    .badge-escalate {
        background: rgba(249,115,22,0.15);
        color: #fb923c;
    }

    .badge-success {
        background: rgba(34,197,94,0.15);
        color: #4ade80;
    }

    </style>
    """, unsafe_allow_html=True)


def render_metrics():

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Framework", "LangChain")

    with col2:
        st.metric("Workflow", "LangGraph")

    with col3:
        st.metric("Vector DB", "ChromaDB")

    with col4:
        st.metric("LLM", "Ollama")


# ================================
# PDF INGESTION
# ================================

def ingest_from_sidebar():

    st.sidebar.subheader("📂 Knowledge Base")

    uploaded_pdf = st.sidebar.file_uploader(
        "📄 Upload PDF",
        type=["pdf"]
    )

    reset_collection = st.sidebar.checkbox(
        "Reset previous knowledge base",
        value=True
    )

    if st.sidebar.button(
        "📥 Ingest PDF",
        use_container_width=True
    ):

        if uploaded_pdf is None:
            st.sidebar.error("Please upload a PDF.")
            return

        settings = Settings.from_env(ROOT)

        try:

            upload_dir = ROOT / "data" / "uploaded"
            upload_dir.mkdir(parents=True, exist_ok=True)

            pdf_path = upload_dir / uploaded_pdf.name

            with open(pdf_path, "wb") as f:
                f.write(uploaded_pdf.getbuffer())

            pages, chunks = ingest_pdf(
                pdf_path,
                settings,
                reset_collection=reset_collection
            )

            st.cache_resource.clear()

            st.sidebar.success(
                f"✅ Ingested {pages} pages and {chunks} chunks."
            )

        except Exception as exc:
            st.sidebar.error(f"❌ {exc}")


# ================================
# CHAT
# ================================

def render_chat(human_reply: str):

    for message in st.session_state.messages:

        with st.chat_message(message["role"]):

            st.markdown(message["content"])

            if message.get("meta"):
                st.caption(message["meta"])

            if message.get("sources"):
                st.caption(
                    "📑 Sources: "
                    + ", ".join(message["sources"])
                )

    query = st.chat_input(
        "💬 Ask a customer support question..."
    )

    if not query:
        return

    st.session_state.messages.append(
        {
            "role": "user",
            "content": query
        }
    )

    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):

        start = time.time()

        with st.spinner("🤖 Thinking..."):

            try:
                result = run_query(query, human_reply)

            except Exception as exc:

                error_text = f"❌ {exc}"

                st.error(error_text)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": error_text
                    }
                )

                return

        end = time.time()

        answer = result.get(
            "answer",
            "No answer generated."
        )

        intent = result.get("intent", "unknown")
        route = result.get("route", "unknown")
        confidence = float(
            result.get("confidence", 0.0)
        )

        reason = result.get(
            "escalation_reason",
            "n/a"
        )

        sources = result.get("sources", [])

        # ---------------- TYPING EFFECT ---------------- #

        placeholder = st.empty()

        typed = ""

        for word in answer.split():
            typed += word + " "
            placeholder.markdown(typed + "▌")
            time.sleep(0.015)

        placeholder.markdown(typed)

        # ---------------- BADGES ---------------- #

        badge_class = (
            "badge-success"
            if route == "auto_answer"
            else "badge-escalate"
        )

        st.markdown(f"""
        <span class="badge badge-tech">
        intent: {intent}
        </span>

        <span class="badge {badge_class}">
        route: {route}
        </span>
        """, unsafe_allow_html=True)

        st.caption(
            f"Confidence: {confidence:.2f} | "
            f"Reason: {reason} | "
            f"Response Time: {end-start:.2f}s"
        )

        # ---------------- SOURCES ---------------- #

        if sources:

            st.markdown("### 📚 Source References")

            for source in sources:

                st.markdown(f"""
                <div style="
                    background: rgba(255,255,255,0.03);
                    padding: 12px;
                    border-radius: 12px;
                    margin-bottom: 10px;
                    border: 1px solid rgba(255,255,255,0.06);
                ">
                    📘 {source}
                </div>
                """, unsafe_allow_html=True)

        # ---------------- RETRIEVED CONTEXT ---------------- #

        with st.expander("📄 Retrieved Context"):

            chunks = result.get(
                "retrieved_chunks",
                []
            )

            if not chunks:
                st.write("No chunks returned.")

            for chunk in chunks:

                page = chunk.get("page", "?")

                score = float(
                    chunk.get("score", 0.0)
                )

                content = str(
                    chunk.get("content", "")
                )

                snippet = (
                    content[:400]
                    + ("..." if len(content) > 400 else "")
                )

                st.markdown(f"""
                ### 📘 Page {page}

                Similarity Score:
                `{score:.2f}`
                """)

                st.write(snippet)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer,
                "meta":
                f"intent={intent} | "
                f"route={route}",
                "sources": sources,
            }
        )


# ================================
# MAIN
# ================================

def main():

    st.set_page_config(
        page_title="RAG Support Assistant",
        page_icon="🤖",
        layout="wide",
    )

    inject_custom_css()

    init_state()

    # ---------------- HEADER ---------------- #

    st.markdown("""
    <div class="main-title">
        🤖 RAG Customer Support Assistant
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="subtitle">
     AI assistant powered by
    LangChain, LangGraph, ChromaDB,
    and Ollama.
    </div>
    """, unsafe_allow_html=True)

    render_metrics()

    st.divider()

    # ---------------- SIDEBAR ---------------- #

    ingest_from_sidebar()

    st.sidebar.subheader("🧠 HITL")

    human_reply = st.sidebar.text_area(
        "Human response during escalation",
        placeholder=
        "Type manual support response..."
    )

    st.sidebar.markdown("---")

    st.sidebar.success("🟢 AI System Online")

    if st.sidebar.button(
        "🗑️ Clear Chat",
        use_container_width=True
    ):

        st.session_state.messages = []
        st.rerun()

    # ---------------- CHAT ---------------- #

    render_chat(human_reply)

    # ---------------- FOOTER ---------------- #

    st.markdown("---")

    st.caption(
        "Built using LangChain • "
        "LangGraph • "
        "ChromaDB • "
        "Ollama"
    )


# ================================
# ENTRY POINT
# ================================

if __name__ == "__main__":

    if not _is_streamlit_runtime():

        print(
            "Run using:\n"
            "streamlit run streamlit_app.py"
        )

        raise SystemExit(0)

    main()
