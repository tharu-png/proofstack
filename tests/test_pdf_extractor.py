
import fitz
import pytest

from app.services.pdf_extractor import extract_pdf_pages


def create_test_pdf() -> bytes:
    document = fitz.open()

    first_page = document.new_page()
    first_page.insert_text((72, 72), "ProofStack evidence on page one.")

    second_page = document.new_page()
    second_page.insert_text((72, 72), "ProofStack evidence on page two.")

    pdf_bytes = document.tobytes()
    document.close()

    return pdf_bytes


def test_extracts_text_and_preserves_page_numbers():
    pdf_bytes = create_test_pdf()

    pages = extract_pdf_pages(pdf_bytes)

    assert len(pages) == 2
    assert pages[0]["page_number"] == 1
    assert "page one" in pages[0]["text"]
    assert pages[1]["page_number"] == 2
    assert "page two" in pages[1]["text"]


def test_rejects_invalid_pdf():
    with pytest.raises(ValueError, match="valid PDF"):
        extract_pdf_pages(b"this is not a PDF")
