from pathlib import Path
from typing import Dict, List, Any
import pypdf


class PDFParser:
    """Multi-page PDF parser with encryption check and form fields support."""

    @staticmethod
    def parse_pdf(file_path: str) -> Dict[str, Any]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found at {file_path}")

        try:
            reader = pypdf.PdfReader(str(path))
        except Exception as exc:
            raise ValueError(f"Failed to parse PDF: Corrupted or unreadable format ({exc})")

        if reader.is_encrypted:
            raise ValueError("The uploaded PDF is password-protected. Please upload an unlocked PDF.")

        num_pages = len(reader.pages)
        if num_pages == 0:
            raise ValueError("The uploaded PDF contains no pages.")

        extracted_text = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            extracted_text.append({
                "page_number": i + 1,
                "text": page_text,
            })

        # Check for interactive AcroForm fields
        form_fields = {}
        try:
            fields = reader.get_fields()
            if fields:
                for k, v in fields.items():
                    val = v.get("/V")
                    if val is not None:
                        form_fields[k] = str(val)
        except Exception:
            pass

        full_text = "\n\n".join(p["text"] for p in extracted_text)

        return {
            "num_pages": num_pages,
            "pages": extracted_text,
            "full_text": full_text,
            "form_fields": form_fields,
            "is_scanned_likely": len(full_text.strip()) < 50 * num_pages,
        }
