# RAG Customer Support Assistant (LangGraph + HITL)

This project implements a production-style Retrieval-Augmented Generation (RAG) customer support assistant with:

- PDF ingestion pipeline
- Chunking + embedding + ChromaDB vector storage
- LangGraph workflow orchestration
- Intent-based routing
- Human-in-the-Loop (HITL) escalation
- Groq LLM integration for final response generation

## 1) Why this project exists

Customer support teams need fast, context-aware responses, but:

- Static FAQ bots miss document context
- LLM-only bots hallucinate without grounding
- Not every query should be answered automatically

This system combines retrieval + controlled workflow + escalation policy.

## 2) Quick start (Windows PowerShell with venv)

### Step 1: Create venv and install packages

```powershell
cd d:\Final
.\scripts\setup_venv.ps1
```

### Step 2: Configure environment

```powershell
Copy-Item .env.example .env
```

Edit `.env` and set:

- `GROQ_API_KEY`
- Optional model/tuning settings

### Step 3: Generate sample PDF knowledge base

```powershell
.\.venv\Scripts\Activate.ps1
python scripts\generate_sample_kb_pdf.py
```

This creates `data/customer_support_kb.pdf`.

### Step 4: Ingest PDF into ChromaDB

```powershell
python app.py ingest --pdf data/customer_support_kb.pdf --reset
```

### Step 5: Ask one question

```powershell
python app.py ask "How can I reset my password?"
```

### Step 6: Interactive chat mode

```powershell
python app.py chat
```

If escalation is needed, you will be prompted for a human response.

### Step 7: Streamlit web app

```powershell
streamlit run streamlit_app.py
```

Note:

- The project includes `.streamlit/config.toml` with `fileWatcherType = "none"` to prevent noisy optional `torchvision` tracebacks from `transformers` while running Streamlit.

Web app features:

- Upload or select a PDF and ingest from the sidebar
- Chat-based customer support interface
- Debug details for intent, route, confidence, and sources
- HITL text area for escalation responses

## 3) Build required deliverable PDFs

```powershell
python scripts\build_pdfs.py
```

This generates:

- `docs/HLD.pdf`
- `docs/LLD.pdf`
- `docs/Technical_Documentation.pdf`

## 4) Validate implementation

Run unit tests:

```powershell
pytest -q
```

Run implementation crosscheck:

```powershell
python scripts\crosscheck.py
```

## 5) Project structure

```text
.
|-- app.py
|-- streamlit_app.py
|-- .streamlit/
|   `-- config.toml
|-- requirements.txt
|-- .env.example
|-- src/
|   `-- rag_support/
|       |-- config.py
|       |-- ingest.py
|       |-- retrieval.py
|       |-- routing.py
|       |-- workflow.py
|       |-- hitl.py
|       |-- cli.py
|       |-- prompts.py
|       `-- schemas.py
|-- scripts/
|   |-- setup_venv.ps1
|   |-- generate_sample_kb_pdf.py
|   |-- build_pdfs.py
|   `-- crosscheck.py
|-- docs/
|   |-- HLD.md
|   |-- LLD.md
|   `-- TECHNICAL_DOCUMENTATION.md
|-- data/
|   `-- customer_support_kb.pdf (generated)
`-- tests/
    `-- test_routing.py
```

## 6) Runtime behavior summary

- Ingestion: PDF -> chunks -> embeddings -> Chroma collection
- Query: retrieve top-k chunks + score -> detect intent -> decide route
- Route `auto_answer`: call Groq with grounded prompt
- Route `escalate`: collect human response (HITL) and return it as final output