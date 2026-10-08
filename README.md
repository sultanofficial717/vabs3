# Vineland-3 Clinical Decision-Support System

A local, privacy-first clinical decision-support application that converts patient inputs (intake form, PDF documents, and scanned images) into structured, evidence-grounded Vineland-3 clinical reports with dual PDF and DOCX export.

---

## 🏗️ Architecture Overview

The system strictly follows a 6-layer modular architecture:

```
Vineland3_Assessment/
├── app/
│   ├── config.py                 # Central configurations & thresholds
│   ├── schemas.py                # Strict Pydantic v2 schemas across all layers
│   ├── main.py                   # FastAPI REST API with endpoints for all layers
│   ├── ingestion/                # Layer 1: Ingestion, file validation, storage, PDF/raster parsing
│   │   ├── validator.py
│   │   └── parser.py
│   ├── verification/             # Layer 2: VLM intake gate (legibility, confidence, issues)
│   │   ├── verifier.py
│   │   └── prompts.py
│   ├── scoring/                  # Layer 3: Deterministic scoring engine (SS, ABC, CI, percentiles)
│   │   └── engine.py
│   ├── rag/                      # Layer 4: ChromaDB persistent vector knowledge base & retriever
│   │   ├── store.py
│   │   └── retriever.py
│   ├── report/                   # Layer 5: Evidence-grounded clinical report generator
│   │   ├── generator.py
│   │   └── prompts.py
│   └── export/                   # Layer 6: Dual identical export engines
│       ├── pdf_exporter.py       # ReportLab PDF generator
│       └── docx_exporter.py      # python-docx DOCX generator
├── scripts/
│   └── ingest_manual.py          # Offline manual indexing into ChromaDB
├── prompts/
│   ├── verifier_prompt.txt       # Exact VLM verifier gate prompt
│   └── report_generator_prompt.txt # Exact LLM report generator prompt
├── tests/
│   ├── test_scoring.py           # Unit tests for deterministic scoring
│   ├── test_schemas.py           # Unit tests for Pydantic schemas
│   ├── test_retrieval_filter.py  # Unit tests for ChromaDB domain filtering & reranking
│   ├── test_end_to_end.py        # End-to-end integration test
│   └── test_api.py               # FastAPI endpoint tests
├── streamlit_app.py              # Clinician dashboard UI
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation & Setup

### 1. Prerequisites
- Python 3.11
- `uv` (recommended) or standard `pip`

### 2. Environment Setup
```bash
# Clone the repository and enter directory
cd "C:\Users\Sulman\Documents\Thesis Work\Vineland3_Assessment"

# Install dependencies using uv (or pip)
uv pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env` and set your API keys if using cloud providers:
```bash
GROQ_API_KEY=your_groq_api_key_here
```
> **Offline Support**: The system is fully equipped with high-fidelity, deterministic offline fallbacks for verification and report generation. It functions completely out of the box even without cloud API keys or when offline.

---

## 🚀 Step-by-Step Execution Guide

### Step 1: Ingest the Vineland-3 Manual into Persistent ChromaDB
Run the offline ingestion script to chunk and index the licensed Vineland-3 manual into ChromaDB:
```bash
python scripts/ingest_manual.py
```
*Creates a persistent Chroma collection named `vineland_manual` in `data/chroma_db/` with local `all-MiniLM-L6-v2` embeddings.*

### Step 2: Run the Automated Test Suite
Execute the full test suite including scoring unit tests, schema validation, RAG filters, and end-to-end pipeline:
```bash
pytest -v tests
```
*Expected: 13 passed tests.*

### Step 3: Launch the FastAPI Backend
Start the REST API server:
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive API documentation: `http://localhost:8000/docs`

### Step 4: Launch the Streamlit Clinician Dashboard
Start the clinician-facing web UI:
```bash
streamlit run streamlit_app.py
```
Open your browser at `http://localhost:8501`.

---

## 🔒 Privacy & Non-Functional Guarantees

1. **Local-Only Storage**: Raw files, metadata, vectors, and generated reports reside strictly in `data/submissions/{uuid}/`.
2. **Zero Identifier Logging**: Patient IDs, names, and protected health information (PHI) are strictly filtered out of system loggers.
3. **Purge Submission Action**: Clinicians can purge all files for a submission at any time via the UI or `DELETE /api/v1/submissions/{submission_id}`.
4. **Deterministic Math**: All standard scores, adaptive levels, percentile ranks, and composite scores are calculated strictly in Python code, preventing LLM arithmetic hallucination.
5. **Pure Grounding**: Every interpretive statement in the generated report cites a specific retrieved chunk ID (`[Chunk: <id>]`) or explicitly states "insufficient evidence".
6. **Clinical Decision Support Only**: All reports contain non-diagnostic disclaimers highlighting that the outputs are intended solely for licensed clinicians.