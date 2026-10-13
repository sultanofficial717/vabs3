import os
import uuid
import html
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from backend.app.config import Config


def xml_safe(val: Any) -> str:
    """Escapes text for ReportLab Paragraph XML parser."""
    if val is None:
        return "-"
    return html.escape(str(val))


class PDFReportBuilder:
    """
    Builds structured, publication-grade clinical assessment PDF reports for Autism Lens.
    """

    @classmethod
    def generate_report(
        cls,
        assessment_data: Dict[str, Any],
        narrative_text: str,
        output_dir: str = None,
    ) -> tuple[str, str]:
        """
        Generates clinical PDF report.
        Returns: (output_filepath, assessment_id)
        """
        output_folder = Path(output_dir or Config.REPORT_FOLDER)
        output_folder.mkdir(parents=True, exist_ok=True)

        assessment_id = assessment_data.get("assessment_id") or uuid.uuid4().hex[:12].upper()
        filename = f"AutismLens_Report_{assessment_id}.pdf"
        filepath = output_folder / filename

        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=40,
            bottomMargin=40,
        )

        styles = getSampleStyleSheet()

        # Custom Clinical Styles
        primary_color = colors.HexColor("#1A365D")  # Deep Navy
        secondary_color = colors.HexColor("#0D9488")  # Deep Teal
        text_color = colors.HexColor("#1F2937")  # Charcoal

        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=primary_color,
            spaceAfter=2,
        )
        subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#4B5563"),
        )
        h2_style = ParagraphStyle(
            "Heading2Custom",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=primary_color,
            spaceBefore=10,
            spaceAfter=4,
        )
        body_style = ParagraphStyle(
            "BodyCustom",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=text_color,
        )
        body_bold = ParagraphStyle(
            "BodyBold",
            parent=body_style,
            fontName="Helvetica-Bold",
        )
        disclaimer_style = ParagraphStyle(
            "DisclaimerCustom",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=7.5,
            leading=10.5,
            textColor=colors.HexColor("#7F1D1D"),
        )

        elements = []

        # 1. Header Banner
        header_table = Table(
            [
                [
                    Paragraph("AUTISM LENS CLINICAL DECISION-SUPPORT REPORT", title_style),
                    Paragraph(
                        f"<b>CONFIDENTIAL MEDICAL RECORD</b><br/>ID: {xml_safe(assessment_id)}<br/>Date: {datetime.now().strftime('%Y-%m-%d')}",
                        subtitle_style,
                    ),
                ]
            ],
            colWidths=[380, 160],
        )
        header_table.setStyle(
            TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ])
        )
        elements.append(header_table)
        elements.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceBefore=4, spaceAfter=8))

        # 2. Patient Demographics & Intake
        patient = assessment_data.get("patient_info", {})
        scores = assessment_data.get("scores", {})
        domains = scores.get("domains", {})
        subdomains = scores.get("subdomains", {})
        comp = scores.get("composite", {})
        patterns = assessment_data.get("patterns", {})

        patient_rows = [
            [
                Paragraph("<b>Patient Name:</b>", body_style),
                Paragraph(xml_safe(patient.get("name", "N/A")), body_style),
                Paragraph("<b>Age:</b>", body_style),
                Paragraph(f"{xml_safe(patient.get('age_years', 'N/A'))}y {xml_safe(patient.get('age_months', 0))}m", body_style),
                Paragraph("<b>Sex:</b>", body_style),
                Paragraph(xml_safe(patient.get("sex", "N/A")), body_style),
            ],
            [
                Paragraph("<b>Respondent:</b>", body_style),
                Paragraph(f"{xml_safe(patient.get('respondent', 'N/A'))} ({xml_safe(patient.get('relationship', 'Parent'))})", body_style),
                Paragraph("<b>Test Date:</b>", body_style),
                Paragraph(xml_safe(patient.get("test_date", "N/A")), body_style),
                Paragraph("<b>Verification:</b>", body_style),
                Paragraph("<font color='#047857'><b>VERIFIED CLINICIAN INPUT</b></font>", body_style),
            ],
            [
                Paragraph("<b>Referral Reason:</b>", body_style),
                Paragraph(xml_safe(patient.get("referral", "Developmental evaluation")), body_style),
                "", "", "", "",
            ]
        ]
        p_table = Table(patient_rows, colWidths=[90, 140, 50, 70, 50, 140])
        p_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("SPAN", (1, 2), (5, 2)),
            ])
        )
        elements.append(p_table)
        elements.append(Spacer(1, 6))

        # 3. Domain Standard Scores Table
        elements.append(Paragraph("1. Vineland-3 Normative Domain Standard Scores (Mean = 100, SD = 15)", h2_style))
        domain_headers = [
            Paragraph("<b>Domain</b>", body_bold),
            Paragraph("<b>Standard Score</b>", body_bold),
            Paragraph("<b>Percentile Rank</b>", body_bold),
            Paragraph("<b>90% Confidence Interval</b>", body_bold),
            Paragraph("<b>Normative Classification</b>", body_bold),
        ]
        dom_data = [domain_headers]
        for dcode in ["COM", "DLS", "SOC", "MOT"]:
            dinfo = domains.get(dcode, {})
            ci_90 = dinfo.get("ci", {}).get("90", {}).get("text", "-")
            dom_data.append([
                Paragraph(xml_safe(dinfo.get("name", dcode)), body_style),
                Paragraph(xml_safe(dinfo.get("ss", "-")), body_style),
                Paragraph(xml_safe(dinfo.get("percentile", "-")), body_style),
                Paragraph(xml_safe(ci_90), body_style),
                Paragraph(f"<b>{xml_safe(dinfo.get('band', '-'))}</b>", body_style),
            ])

        # ABC Composite Row
        abc_val = comp.get("abc", "-")
        abc_pct = comp.get("percentile", "-")
        abc_ci = comp.get("ci", {}).get("90", {}).get("text", "-")
        abc_band = comp.get("abc_band", "-")
        dom_data.append([
            Paragraph("<b>Adaptive Behavior Composite (ABC)</b>", body_bold),
            Paragraph(f"<b>{xml_safe(abc_val)}</b>", body_bold),
            Paragraph(f"<b>{xml_safe(abc_pct)}</b>", body_bold),
            Paragraph(f"<b>{xml_safe(abc_ci)}</b>", body_bold),
            Paragraph(f"<b>{xml_safe(abc_band)}</b>", body_bold),
        ])

        dom_table = Table(dom_data, colWidths=[160, 85, 85, 100, 110])
        dom_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A365D")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E0F2FE")),
            ])
        )
        elements.append(dom_table)
        elements.append(Spacer(1, 6))

        # 4. Subdomain Scores Table
        elements.append(Paragraph("2. Subdomain v-Scale Scores & Developmental Equivalents (Mean = 15, SD = 3)", h2_style))
        sub_headers = [
            Paragraph("<b>Subdomain</b>", body_bold),
            Paragraph("<b>Domain</b>", body_bold),
            Paragraph("<b>Raw</b>", body_bold),
            Paragraph("<b>v-Scale</b>", body_bold),
            Paragraph("<b>Age Equivalent</b>", body_bold),
            Paragraph("<b>Growth Scale (GSV)</b>", body_bold),
        ]
        sub_data = [sub_headers]
        for scode in ["rec", "exp", "wrn", "per", "dom", "cmm", "ipr", "pla", "cop", "gmo", "fmo"]:
            sinfo = subdomains.get(scode, {})
            sub_data.append([
                Paragraph(xml_safe(sinfo.get("name", scode)), body_style),
                Paragraph(xml_safe(sinfo.get("domain", "")), body_style),
                Paragraph(xml_safe(sinfo.get("raw", "-")), body_style),
                Paragraph(xml_safe(sinfo.get("v", "-")), body_style),
                Paragraph(xml_safe(sinfo.get("age_equiv", "-")), body_style),
                Paragraph(xml_safe(sinfo.get("gsv", "-")), body_style),
            ])

        sub_table = Table(sub_data, colWidths=[150, 70, 60, 70, 100, 90])
        sub_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0D9488")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ])
        )
        elements.append(sub_table)
        elements.append(Spacer(1, 6))

        # 5. ASD Pattern Engine Findings
        elements.append(Paragraph("3. ASD Pattern Engine Analysis (DSM-5-TR Grounded)", h2_style))
        likelihood = patterns.get("asd_profile_likelihood", {})
        badge_color = colors.HexColor("#DC2626") if likelihood.get("color") == "danger" else colors.HexColor("#D97706")
        
        pat_summary = [
            [
                Paragraph("<b>Profile Likelihood:</b>", body_bold),
                Paragraph(f"<b><font color='{badge_color.hexval()}'>{xml_safe(likelihood.get('label', 'Analyzed'))}</font></b>", body_style),
            ],
            [
                Paragraph("<b>Clinical Description:</b>", body_bold),
                Paragraph(xml_safe(likelihood.get("description", "Evaluation of score order and subdomain scatter.")), body_style),
            ]
        ]
        pat_table = Table(pat_summary, colWidths=[110, 430])
        pat_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FEF2F2") if likelihood.get("color") == "danger" else colors.HexColor("#FFFBEB")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#FCA5A5") if likelihood.get("color") == "danger" else colors.HexColor("#FDE68A")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ])
        )
        elements.append(pat_table)
        elements.append(Spacer(1, 6))

        # 6. Clinical Narrative Sections
        elements.append(Paragraph("4. Clinical Narrative Interpretation & Recommendations", h2_style))
        paragraphs = narrative_text.split("\n\n")
        for p in paragraphs:
            p_text = p.strip()
            if not p_text:
                continue
            if p_text.startswith("### ") or p_text.startswith("## "):
                clean_title = p_text.lstrip("#").strip()
                elements.append(Paragraph(f"<b>{xml_safe(clean_title)}</b>", h2_style))
                elements.append(Spacer(1, 2))
            else:
                # Format body paragraph with bolding where appropriate
                safe_body = xml_safe(p_text)
                # Re-apply bolding for markdown **text**
                import re
                formatted_body = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", safe_body)
                elements.append(Paragraph(formatted_body, body_style))
                elements.append(Spacer(1, 4))

        # 7. Signature & Safeguard Block
        elements.append(Spacer(1, 10))
        sig_data = [
            [
                Paragraph("<b>Evaluating Clinician / Neuropsychologist:</b><br/><br/>____________________________________<br/>Signature & License Number", body_style),
                Paragraph("<b>Countersigning Supervisor:</b><br/><br/>____________________________________<br/>Signature & Credentials", body_style),
            ]
        ]
        sig_table = Table(sig_data, colWidths=[270, 270])
        sig_table.setStyle(
            TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ])
        )
        elements.append(KeepTogether(sig_table))

        # Disclaimer
        elements.append(Spacer(1, 8))
        disclaimer_text = (
            "NOTICE: Autism Lens is a clinical decision-support tool developed for research and clinical workflow optimization. "
            "It does NOT independently provide an autism diagnosis. Final diagnosis requires multidisciplinary evaluation, clinical history, "
            "and direct observation according to DSM-5-TR standards."
        )
        elements.append(Paragraph(xml_safe(disclaimer_text), disclaimer_style))

        # Build PDF
        doc.build(elements)
        return str(filepath), assessment_id
