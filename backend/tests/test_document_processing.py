import pytest
import numpy as np
import io
from PIL import Image
from pypdf import PdfWriter
from backend.app.document_processing.image_preprocessor import ImagePreprocessor
from backend.app.document_processing.pdf_parser import PDFParser
from backend.app.document_processing.extractor import DocumentExtractor


def test_image_preprocessing(tmp_path):
    # Create synthetic test image
    img = np.ones((200, 300, 3), dtype=np.uint8) * 255
    # Draw some text-like lines
    img[50:60, 50:250] = 0
    img[90:100, 50:250] = 0
    img_path = str(tmp_path / "test_sheet.png")
    Image.fromarray(img).save(img_path)

    loaded = ImagePreprocessor.load_image(img_path)
    assert loaded is not None
    assert loaded.shape == (200, 300, 3)

    preprocessed = ImagePreprocessor.preprocess_for_ocr(loaded)
    assert "binary" in preprocessed
    assert "deskewed" in preprocessed
    assert preprocessed["height"] == 200


def test_pdf_parsing_and_extraction(tmp_path):
    # Create simple PDF using pypdf
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    pdf_path = str(tmp_path / "clinical_report.pdf")
    with open(pdf_path, "wb") as f:
        writer.write(f)

    parsed = PDFParser.parse_pdf(pdf_path)
    assert parsed["num_pages"] == 1
    assert parsed["is_scanned_likely"] is True

    # Test extraction
    res = DocumentExtractor.extract_from_file(pdf_path)
    assert res["source_type"] == "pdf"
    assert "patient_info" in res
    assert "raw_scores" in res
