"""
streamlit_app.py
Interactive, clinician-facing Streamlit Dashboard for the Vineland-3 Clinical Decision Support System.
Provides intake ingestion, verification gate review, deterministic scoring, RAG inspection,
structured clinical report viewing, identical PDF/DOCX downloads, and privacy deletion.
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path

from app.schemas import ClinicalFormData
from app.ingestion.validator import SubmissionValidator, StoredFileMetadata
from app.ingestion.parser import DocumentParser
from app.verification.verifier import InputVerifier
from app.scoring.engine import ScoringEngine
from app.rag.retriever import KnowledgeRetriever
from app.report.generator import ReportGenerator
from app.export.pdf_exporter import export_report_to_pdf
from app.export.docx_exporter import export_report_to_docx
from app.config import SUBMISSIONS_DIR

# Set page config
st.set_page_config(
    page_title="Vineland-3 Clinical Decision Support",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for clinical styling
st.markdown("""
<style>
    .main-title {
        color: #1B365D;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #4A5568;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    .disclaimer-box {
        background-color: #FFF5F5;
        border-left: 5px solid #E53E3E;
        padding: 1rem;
        border-radius: 4px;
        font-size: 0.9rem;
        color: #742A2A;
    }
</style>
""", unsafe_allow_html=True)

# App Header
st.markdown('<div class="main-title">🩺 Vineland-3 Clinical Decision-Support System</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Privacy-First • Evidence-Grounded • Normative VABS-3 Decision Support</div>', unsafe_allow_html=True)

# Sidebar: System & Privacy Controls
with st.sidebar:
    st.header("🔒 Privacy & System Guardrails")
    st.info(
        "**Local Processing Only**:\n"
        "• Data persists strictly on local machine.\n"
        "• Zero logging of patient identifiers.\n"
        "• Deterministic scoring in code (not LLM).\n"
        "• Every claim grounded in Vineland manual chunks."
    )
    
    st.markdown("---")
    st.subheader("Active Session")
    if "submission_id" in st.session_state:
        st.success(f"UUID: `{st.session_state['submission_id'][:13]}...`")
        if st.button("🗑️ Delete Submission (Purge All Files)", type="primary"):
            sub_id = st.session_state["submission_id"]
            sub_path = SUBMISSIONS_DIR / sub_id
            if sub_path.exists():
                import shutil
                shutil.rmtree(sub_path)
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.warning("All submission data permanently purged.")
            st.rerun()
    else:
        st.write("No active submission loaded.")

# Tabs for workflow stages
tab_intake, tab_verify, tab_scoring, tab_rag, tab_report, tab_export = st.tabs([
    "1. Data Ingestion",
    "2. Verification Gate",
    "3. Deterministic Scoring",
    "4. Knowledge Evidence (RAG)",
    "5. Clinical Report",
    "6. PDF / DOCX Export",
])

# -------------------------------------------------------------
# TAB 1: DATA INGESTION
# -------------------------------------------------------------
with tab_intake:
    st.subheader("Step 1: Patient Intake & Document Ingestion")

    col_form, col_files = st.columns([1.2, 1.0])

    with col_form:
        st.markdown("#### Patient Information & Scores")
        with st.form("intake_form"):
            col_id, col_sex = st.columns(2)
            patient_id = col_id.text_input("Patient ID *", value="PT-84291", help="Clinical subject or record identifier")
            sex = col_sex.selectbox("Sex", options=["Male", "Female", "Other"])

            col_age_yr, col_age_mo = st.columns(2)
            age_years = col_age_yr.number_input("Age (Years)", min_value=0.0, max_value=90.0, value=7.5, step=0.5)
            age_months = col_age_mo.number_input("Age (Total Months, optional)", min_value=0, max_value=1200, value=90)

            informant = st.text_input("Informant / Respondent *", value="Mother", help="Relationship of the person rating the child")

            st.markdown("##### Vineland-3 Domain Standard Scores (Mean=100, SD=15)")
            col_comm, col_dls = st.columns(2)
            comm_score = col_comm.number_input("Communication Score", min_value=20, max_value=160, value=68, step=1)
            dls_score = col_dls.number_input("Daily Living Skills Score", min_value=20, max_value=160, value=74, step=1)

            col_soc, col_mot = st.columns(2)
            soc_score = col_soc.number_input("Socialization Score", min_value=20, max_value=160, value=65, step=1)
            motor_score = col_mot.number_input("Motor Skills Score (optional for age >= 10)", min_value=20, max_value=160, value=82, step=1)

            free_text = st.text_area(
                "Clinical Observations & Intake Notes",
                value="Teacher notes significant difficulty with spontaneous peer socialization. Needs routine assistance with personal grooming and buttoning.",
                height=100,
            )

            submit_btn = st.form_submit_button("🚀 Submit & Ingest Intake Data", type="primary")

    with col_files:
        st.markdown("#### Supplemental Clinical Files (Optional)")
        uploaded_pdf = st.file_uploader(
            "Upload Vineland Assessment PDF (Max 1 file, <=25MB)",
            type=["pdf"],
            help="Uploaded PDF will be parsed with pdfplumber (or rasterized to VLM if non-text).",
        )
        uploaded_images = st.file_uploader(
            "Upload Scanned Protocol Images (JPG / PNG)",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            help="Uploaded images are verified through the VLM intake gate.",
        )

    if submit_btn:
        if not patient_id or not informant:
            st.error("Patient ID and Informant are mandatory fields.")
        else:
            with st.spinner("Validating and storing files locally..."):
                form_data = ClinicalFormData(
                    patient_id=patient_id,
                    age_years=age_years,
                    age_months=age_months,
                    sex=sex,
                    informant=informant,
                    communication_score=comm_score,
                    daily_living_skills_score=dls_score,
                    socialization_score=soc_score,
                    motor_skills_score=motor_score,
                    free_text_observations=free_text,
                )

                pdf_bytes = uploaded_pdf.read() if uploaded_pdf else None
                pdf_name = uploaded_pdf.name if uploaded_pdf else None

                image_list = []
                if uploaded_images:
                    for img in uploaded_images:
                        image_list.append((img.name, img.read()))

                try:
                    sub_id, stored_files, warnings = SubmissionValidator.validate_and_store(
                        form_data=form_data,
                        pdf_bytes=pdf_bytes,
                        pdf_filename=pdf_name,
                        image_files=image_list,
                    )
                    st.session_state["submission_id"] = sub_id
                    st.session_state["form_data"] = form_data
                    st.session_state["stored_files"] = stored_files

                    # Automatically parse pages
                    sub_dir = SUBMISSIONS_DIR / sub_id
                    parsed_pages = []
                    for meta in stored_files:
                        pages = DocumentParser.parse_file(meta, sub_dir / "raster")
                        parsed_pages.extend(pages)
                    st.session_state["parsed_pages"] = parsed_pages

                    st.success(f"Intake successfully ingested! Assigned UUID: `{sub_id}`")
                    st.info(f"Stored {len(stored_files)} files ({len(parsed_pages)} total pages). Proceeding to Verification Gate.")
                except Exception as e:
                    st.error(f"Ingestion failed: {e}")

# -------------------------------------------------------------
# TAB 2: VERIFICATION GATE
# -------------------------------------------------------------
with tab_verify:
    st.subheader("Step 2: VLM/LLM Input Verification Gate")
    if "submission_id" not in st.session_state:
        st.info("Please submit patient intake data in Step 1 first.")
    else:
        st.write(f"Evaluating submission: `{st.session_state['submission_id']}`")
        if st.button("🔍 Run VLM Verification Gate", type="primary") or "verification_response" in st.session_state:
            if "verification_response" not in st.session_state:
                with st.spinner("Running verification gate on all document pages..."):
                    verifier = InputVerifier()
                    verif_resp = verifier.verify_submission(
                        st.session_state["submission_id"],
                        st.session_state.get("parsed_pages", []),
                    )
                    st.session_state["verification_response"] = verif_resp

            verif_resp = st.session_state["verification_response"]

            col_v1, col_v2, col_v3 = st.columns(3)
            with col_v1:
                st.metric("Gate Status", "PASSED" if verif_resp.overall_passed else "REJECTED / FLAGGED")
            with col_v2:
                st.metric("Input Quality Index", f"{verif_resp.input_quality_score:.2f} / 1.00")
            with col_v3:
                st.metric("Evaluated Pages", len(verif_resp.results))

            if verif_resp.rejections:
                st.error("### Rejections / Critical Gate Issues:")
                for rej in verif_resp.rejections:
                    st.write(f"❌ {rej}")

            if verif_resp.audit_flags:
                st.warning("### Audit Observations:")
                for flag in verif_resp.audit_flags:
                    st.write(f"⚠️ {flag}")

            if verif_resp.results:
                st.markdown("#### Page-by-Page Extraction Audit")
                for r in verif_resp.results:
                    with st.expander(f"File: {r.file_name} (Page {r.page_number or 1}) - Confidence: {r.confidence:.2f}"):
                        st.write(f"**Valid Clinical Document**: {r.is_valid_clinical_document}")
                        st.write(f"**Content Type**: {r.content_type}")
                        st.write(f"**Legible**: {r.legible}")
                        st.write(f"**Passed Gate**: {r.passed_gate}")
                        st.json(r.extracted_fields.model_dump())

# -------------------------------------------------------------
# TAB 3: DETERMINISTIC SCORING
# -------------------------------------------------------------
with tab_scoring:
    st.subheader("Step 3: Deterministic Scoring Engine (Normative Pearson Tables)")
    if "submission_id" not in st.session_state:
        st.info("Please submit patient intake data in Step 1 first.")
    else:
        if st.button("📊 Calculate Deterministic Scores", type="primary") or "scoring_object" in st.session_state:
            if "scoring_object" not in st.session_state:
                form_data = st.session_state["form_data"]
                verif_resp = st.session_state.get("verification_response")
                scoring_obj = ScoringEngine.score_submission(form_data, verif_resp)
                st.session_state["scoring_object"] = scoring_obj

            scoring_obj = st.session_state["scoring_object"]

            # Key Metric Cards
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Adaptive Behavior Composite (ABC)", f"{scoring_obj.composite.standard_score:.1f}")
            c2.metric("Composite Adaptive Level", scoring_obj.composite.adaptive_level)
            c3.metric("Composite Percentile Rank", f"{scoring_obj.composite.percentile_rank}th")
            c4.metric("Input Quality Index", f"{scoring_obj.input_quality:.2f} / 1.00")

            # Scores Table
            st.markdown("#### Domain Standard Scores Summary")
            rows = []
            for d, s in scoring_obj.domain_scores.items():
                rows.append({
                    "Domain": d,
                    "Standard Score (SS)": f"{s.standard_score:.1f}",
                    "95% Confidence Interval": f"{s.confidence_interval_95[0]} - {s.confidence_interval_95[1]}",
                    "Percentile Rank": f"{s.percentile_rank}th",
                    "Adaptive Level": s.adaptive_level,
                    "Data Source": s.source,
                })
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True)

            # Bar Chart
            st.markdown("#### Domain Standard Scores Profile")
            chart_df = pd.DataFrame({
                "Domain": list(scoring_obj.domain_scores.keys()),
                "Standard Score": [s.standard_score for s in scoring_obj.domain_scores.values()],
            })
            st.bar_chart(chart_df.set_index("Domain"))

            if scoring_obj.flags:
                st.warning("#### Clinical Profile Flags:")
                for f in scoring_obj.flags:
                    st.write(f"🚩 {f}")

# -------------------------------------------------------------
# TAB 4: KNOWLEDGE LAYER (RAG)
# -------------------------------------------------------------
with tab_rag:
    st.subheader("Step 4: Vineland-3 Manual Evidence Retrieval")
    if "scoring_object" not in st.session_state:
        st.info("Please calculate scores in Step 3 first.")
    else:
        if st.button("📚 Retrieve Evidence Passages", type="primary") or "evidence" in st.session_state:
            if "evidence" not in st.session_state:
                with st.spinner("Querying ChromaDB collection 'vineland_manual' with metadata filters..."):
                    retriever = KnowledgeRetriever()
                    evidence = retriever.retrieve_for_scoring_object(st.session_state["scoring_object"])
                    st.session_state["evidence"] = evidence

            evidence = st.session_state["evidence"]
            st.success("Retrieved verified manual passages for each evaluated domain.")

            for dom, chunks in evidence.items():
                with st.expander(f"Domain: {dom} ({len(chunks)} passages retrieved)"):
                    for c in chunks:
                        st.markdown(f"**[{c.chunk_id}] {c.section} ({c.page})** • Score Range: `{c.score_range}` • Similarity: `{c.similarity_score:.3f}`")
                        st.text(c.text[:400] + ("..." if len(c.text) > 400 else ""))
                        st.markdown("---")

# -------------------------------------------------------------
# TAB 5: REPORT GENERATION
# -------------------------------------------------------------
with tab_report:
    st.subheader("Step 5: Evidence-Grounded Clinical Decision Support Report")
    if "scoring_object" not in st.session_state or "evidence" not in st.session_state:
        st.info("Please complete scoring and evidence retrieval in previous steps.")
    else:
        if st.button("📝 Synthesize Clinical Report", type="primary") or "report" in st.session_state:
            if "report" not in st.session_state:
                with st.spinner("Synthesizing clinical report with manual chunk citations..."):
                    generator = ReportGenerator()
                    report = generator.generate_report(
                        submission_id=st.session_state["submission_id"],
                        form_data=st.session_state["form_data"],
                        scoring=st.session_state["scoring_object"],
                        evidence=st.session_state["evidence"],
                        verification_response=st.session_state.get("verification_response"),
                    )
                    st.session_state["report"] = report

            report = st.session_state["report"]

            st.markdown(f"### Assessment Report for Patient `{report.patient_id}`")
            st.caption(f"Evaluation Date: {report.evaluation_date} | Submission: `{report.submission_id}`")

            st.markdown("#### 1. Clinical Summary")
            st.write(report.patient_summary)

            st.markdown("#### 2. Scores Table Narrative")
            st.write(report.scores_table_narrative)

            st.markdown("#### 3. Domain-Wise Interpretations")
            for dom_int in report.domain_interpretations:
                st.markdown(f"**{dom_int.domain} Domain (Standard Score: {dom_int.standard_score:.1f} • {dom_int.adaptive_level})**")
                st.write(dom_int.narrative)
                if dom_int.citations:
                    st.caption("Citations: " + ", ".join(dom_int.citations))

            st.markdown("#### 4. Functional Adaptive Strengths")
            for st_item in report.strengths:
                st.write(f"• {st_item}")

            st.markdown("#### 5. Areas of Concern & Adaptive Deficits")
            for ac_item in report.areas_of_concern:
                st.write(f"• {ac_item}")

            st.markdown("#### 6. Recommendations & Suggested Follow-Up")
            for rec in report.recommendations:
                st.write(f"• {rec}")

            st.markdown("#### 7. Data Quality & Input Verification Notes")
            st.write(report.data_quality_notes)

            st.markdown("#### 8. Cited References")
            ref_data = [{"Chunk ID": r.chunk_id, "Citation": r.citation, "Summary": r.summary} for r in report.references]
            st.table(pd.DataFrame(ref_data))

            st.markdown(f'<div class="disclaimer-box"><b>CLINICAL NOTICE:</b> {report.disclaimer}</div>', unsafe_allow_html=True)

# -------------------------------------------------------------
# TAB 6: EXPORT
# -------------------------------------------------------------
with tab_export:
    st.subheader("Step 6: Export Identical PDF and DOCX Reports")
    if "report" not in st.session_state:
        st.info("Please generate the clinical report in Step 5 before exporting.")
    else:
        report = st.session_state["report"]
        st.write("Both export formats render identically from the validated ClinicalReport schema.")

        col_pdf, col_docx = st.columns(2)

        with col_pdf:
            st.markdown("#### PDF Export (ReportLab)")
            pdf_bytes = export_report_to_pdf(report)
            st.download_button(
                label="📥 Download PDF Report",
                data=pdf_bytes,
                file_name=f"vineland3_report_{report.patient_id}.pdf",
                mime="application/pdf",
                type="primary",
            )
            st.caption("Includes official headers, formatted scores table, qualitative narratives, citations, and disclaimer.")

        with col_docx:
            st.markdown("#### DOCX Export (python-docx)")
            docx_bytes = export_report_to_docx(report)
            st.download_button(
                label="📥 Download DOCX Report",
                data=docx_bytes,
                file_name=f"vineland3_report_{report.patient_id}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary",
            )
            st.caption("Identical layout and structure in Microsoft Word format for clinical notes integration.")
