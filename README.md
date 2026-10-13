# Autism Lens — Clinical Decision-Support System (v2.0)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Framework: Flask](https://img.shields.io/badge/framework-Flask-black.svg)](https://flask.palletsprojects.com/)
[![Pearson Norms: VABS--3](https://img.shields.io/badge/scoring-Pearson_VABS--3_Appendix_B-green.svg)]()
[![Tests: 15 Passed](https://img.shields.io/badge/tests-15%20passed-success.svg)]()

**Autism Lens** is a multimodal clinical decision-support application that converts patient inputs (manual form entry, evaluation PDF documents, and scanned/photographed evaluation sheets) into structured, evidence-grounded Vineland Adaptive Behavior Scales (VABS-3) clinical scores, DSM-5-TR adaptive pattern recognitions, and publication-grade PDF clinical assessment reports.

---

## 🏗️ Architectural Overview

The application features a clean, separated architecture uniting an intuitive, accessible frontend with a robust, deterministic Python/Flask backend:

```
vabs3/
├── backend/
│   ├── app/
│   │   ├── config.py                 # Centralized configuration, storage paths, security
│   │   ├── schemas/                  # Pydantic/dataclass schema validators
│   │   │   └── assessment.py         # Patient demographics, raw scores, and verification schemas
│   │   ├── routes/                   # Clean Flask REST API blueprints
│   │   │   ├── health.py             # GET /api/health
│   │   │   ├── documents.py          # POST /api/documents/extract
│   │   │   └── assessments.py        # POST /api/assessments/validate, score, report
│   │   ├── scoring/                  # Reusable scoring bindings
│   │   ├── document_processing/      # Multimodal intake & computer vision pipeline
│   │   │   ├── image_preprocessor.py # OpenCV deskewing, bilateral filtering, adaptive binarization
│   │   │   ├── pdf_parser.py         # Multi-page PDF text & form-field parser
│   │   │   └── extractor.py          # Intelligent clinical evaluation form extractor
│   │   ├── reports/                  # Clinical report generation
│   │   │   └── pdf_builder.py        # Publication-grade ReportLab PDF generator
│   │   ├── services/                 # Business logic service layer
│   │   │   ├── scoring_service.py    # Authoritative Pearson VABS-3 & DSM-5-TR pattern engine wrapper
│   │   │   └── interpretation_service.py # Groq LLM & deterministic offline clinical synthesis
│   │   └── utils/
│   │       └── file_security.py      # Secure UUID naming, magic bytes check, temp file cleanup
│   ├── tests/                        # Comprehensive automated test suite (15 unit & E2E tests)
│   ├── requirements.txt              # Backend dependencies
│   └── run.py                        # Standalone backend server runner
├── frontend/
│   ├── index.html                    # Single-page application clinical workspace
│   └── static/
│       ├── css/
│       │   └── style.css             # Accessible, clinical design system & responsive layout
│       └── js/
│           ├── api.js                # API service communicating with Flask
│           ├── visualizations.js     # Normative score bars, percentile bands, radar & pattern cards
│           ├── workflow.js           # 7-Step guided workflow state machine
│           └── app.js                # Main frontend application bootstrap
├── scoring.py                        # Pearson VABS-3 Appendix B scoring engine
├── norms.py                          # Appendix B.1 and B.3 normative lookup engine
├── norms_tables.py                   # Official Pearson Tables B.1, B.2, B.3
├── pattern_engine.py                 # DSM-5-TR ASD pattern engine
├── interpreter.py                    # Groq API narrative interpreter
├── items.py & age_markers.py         # Subdomain items metadata & age start markers
├── data/                             # Secure local storage (uploads & reports)
├── .env.example                      # Environment variables template
├── requirements.txt                  # Full project dependencies
└── run.py                            # Unified application entry point
```

---

## 🧭 The 7-Step Clinical Workflow

Autism Lens guides clinicians through an end-to-end validated workflow:

1. **Step 1: Patient Information (Intake)**
   - **Option A (Manual Entry):** Fill in validated patient demographics (ID, Age in Years & Months, Sex, Respondent, Relationship, Test Date, Referral Reason).
   - **Option B (Import From Document):** Route straight to document ingestion.
2. **Step 2: Document Upload (PDF / Image)**
   - Upload PDF, JPEG, or PNG clinical evaluation sheets (up to 25MB).
   - Validates file type and magic bytes to block disguised or malicious files.
   - Preprocesses images with OpenCV (auto-deskewing, noise reduction, Otsu binarization).
   - Automatically extracts patient demographics and scores.
3. **Step 3: Input Verification Gate**
   - **Explicit Verification Stage:** Extracted values are presented in an editable review table.
   - Clinicians can inspect, verify, and correct any extracted score or field before scoring.
   - Prevents scoring until all mandatory inputs are verified.
4. **Step 4: Autism Scoring Engine**
   - Executes deterministic Pearson VABS-3 normative lookup (Appendix B).
   - Computes Standard Scores (SS), Percentile Ranks, and 90% Confidence Intervals for Communication, Daily Living Skills, Socialization, and Motor domains.
   - Computes Adaptive Behavior Composite (ABC).
   - Evaluates intra-individual Strengths & Weaknesses against the child's own mean SS.
   - Runs DSM-5-TR ASD Pattern Engine (Classic ASD, High-Functioning ASD, Severe ASD, Motor Preservation, etc.).
5. **Step 5: Visualizations & Scoring Maps**
   - Interactive Domain Standard Score bar charts against population norms (Mean = 100, SD = 15).
   - Subdomain v-scale breakdown table (Mean = 15, SD = 3) with developmental Age Equivalents and Growth Scale Values (GSV).
   - Intra-individual scatter cards (Strengths / Weaknesses).
   - ASD Profile Likelihood gauge with DSM-5-TR criterion mapping.
6. **Step 6: Clinical Report Generation**
   - Synthesizes an 8-section evidence-grounded clinical narrative.
   - Powered by Groq LLM (`llama-3.3-70b-versatile`) when configured, with a deterministic offline clinical synthesis fallback when offline.
7. **Step 7: Report Preview & PDF Download**
   - In-browser clinical narrative review.
   - Generates and downloads a publication-grade ReportLab PDF containing complete demographic summaries, tables, ASD pattern analysis, recommendations, and countersignature blocks.

---

## ⚙️ Installation & Quickstart

### 1. Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13
- A modern web browser (Chrome, Firefox, Safari, Edge)

### 2. Environment Setup
```bash
# Clone or navigate to the repository
cd /home/talha/projects/vabs3

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*(Optional)* Add your Groq API key in `.env` if you wish to use cloud LLM inference:
```env
GROQ_API_KEY=gsk_your_groq_api_key_here
```
> **100% Offline Support**: If `GROQ_API_KEY` is not provided, Autism Lens automatically engages its deterministic, evidence-grounded clinical narrative synthesis engine. The application functions completely out-of-the-box offline.

### 4. Launch the Application
Run the unified entry point:
```bash
python run.py
```
Open your browser and navigate to:
**`http://localhost:5050`**

---

## 📡 REST API Reference

The backend exposes clean, validated JSON REST APIs:

### `GET /api/health`
Health check and capability introspection.
- **Response `200`:**
  ```json
  {
    "status": "healthy",
    "version": "2.0.0",
    "capabilities": {
      "deterministic_vabs3_scoring": true,
      "asd_pattern_engine": true,
      "opencv_document_preprocessing": true,
      "multipage_pdf_parsing": true,
      "reportlab_pdf_export": true,
      "groq_llm_interpreter": false,
      "deterministic_offline_synthesis": true
    }
  }
  ```

### `GET /api/meta`
Returns structural domain definitions, subdomain items, and age start markers.

### `POST /api/documents/extract`
Uploads a PDF or image file (`multipart/form-data`) and extracts clinical evaluation fields.
- **Payload:** `file` (binary)
- **Response `200`:** Structured patient info, raw scores, extraction confidence %, and warnings.

### `POST /api/assessments/validate`
Validates patient demographics and raw scores prior to scoring.
- **Payload:**
  ```json
  {
    "patient_info": { "name": "PT-101", "age_years": 7, "age_months": 6, "sex": "Male" },
    "raw_scores": { "rec": 28, "exp": 32, "wrn": 14, "per": 38, "dom": 18, "cmm": 12, "ipr": 16, "pla": 12, "cop": 10, "gmo": 36, "fmo": 26 },
    "verified": true
  }
  ```
- **Response `200`:** `{ "ok": true, "verified": true, "cleaned_data": { ... } }`

### `POST /api/assessments/score`
Executes the Pearson normative scoring engine and DSM-5-TR pattern engine.
- **Response `200`:** Standard scores, percentile ranks, confidence intervals, composite ABC, Strengths/Weaknesses, and ASD patterns.

### `POST /api/assessments/report`
Generates an 8-section clinical report narrative and builds the publication PDF.
- **Response `200`:** `{ "ok": true, "assessment_id": "AL-7B93", "narrative": "...", "download_url": "/api/assessments/AL-7B93/report" }`

### `GET /api/assessments/<assessment_id>/report`
Downloads the generated PDF report.

---

## 🧪 Testing & Quality Assurance

Autism Lens includes a comprehensive automated test suite covering unit calculations, schema validations, computer vision preprocessing, and end-to-end workflow execution.

Run the tests using `pytest`:
```bash
PYTHONPATH=. pytest -v backend/tests
```

**Results:**
```
backend/tests/test_document_processing.py::test_image_preprocessing PASSED      [  6%]
backend/tests/test_document_processing.py::test_pdf_parsing_and_extraction PASSED [ 13%]
backend/tests/test_end_to_end.py::test_full_workflow_end_to_end PASSED          [ 20%]
backend/tests/test_health.py::test_health_endpoint PASSED                       [ 26%]
backend/tests/test_health.py::test_metadata_endpoint PASSED                     [ 33%]
backend/tests/test_pattern_engine.py::test_classic_asd_pattern PASSED           [ 40%]
backend/tests/test_pattern_engine.py::test_high_functioning_pattern PASSED      [ 46%]
backend/tests/test_pattern_engine.py::test_severe_asd_pattern PASSED            [ 53%]
backend/tests/test_reports.py::test_narrative_synthesis_offline PASSED          [ 60%]
backend/tests/test_reports.py::test_pdf_report_generation PASSED                [ 66%]
backend/tests/test_scoring.py::test_scoring_known_profile PASSED                [ 73%]
backend/tests/test_validation.py::test_validate_patient_info_valid PASSED        [ 80%]
backend/tests/test_validation.py::test_validate_patient_info_missing_name PASSED [ 86%]
backend/tests/test_validation.py::test_validate_patient_info_invalid_age PASSED  [ 93%]
backend/tests/test_validation.py::test_validate_assessment_inputs_missing_scores PASSED [100%]

============================== 15 passed in 0.60s ==============================
```

---

## 🔒 Security, Privacy & Clinical Compliance

1. **Local, Privacy-First Architecture**: Patient data, evaluation sheets, and scores remain on the local server. No patient identifiers are transmitted to third-party services unless cloud Groq inference is explicitly enabled.
2. **Strict File Upload Sanitization**:
   - Filenames are replaced with server-controlled UUIDs.
   - Header magic bytes verification prevents spoofed file extensions.
   - Uploaded documents are processed in isolated directories and cleaned up immediately after extraction.
3. **Clinical Safeguards**:
   - The application explicitly disclaims autonomous diagnostic capability.
   - Displays interpretations strictly supported by validated Pearson normative tables and DSM-5-TR diagnostic criteria.
   - Mandatory clinician countersignature and supervisory review blocks are included on all generated PDF reports.