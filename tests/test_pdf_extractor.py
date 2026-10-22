
import fitz
import pytest

from app.services.pdf_extractor import extract_pdf_pages
from fastapi.testclient import TestClient
from app.main import app

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


def test_upload_pdf_endpoint():
    pdf_bytes = create_test_pdf()
    client = TestClient(app)

    response = client.post(
        "/documents/extract",
        files={
            "file": (
                "evidence.pdf",
                pdf_bytes,
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["filename"] == "evidence.pdf"
    assert data["page_count"] == 2
    assert len(data["pages"]) == 2
    assert data["pages"][0]["page_number"] == 1
    assert "page one" in data["pages"][0]["text"]


def test_rejects_non_pdf_upload():
    client = TestClient(app)

    response = client.post(
        "/documents/extract",
        files={
            "file": (
                "notes.txt",
                b"This is not a PDF.",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Only PDF files are supported."


def test_rejects_invalid_pdf_upload():
    client = TestClient(app)

    response = client.post(
        "/documents/extract",
        files={
            "file": (
                "broken.pdf",
                b"This is not a valid PDF.",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 400
    assert "valid PDF" in response.json()["detail"]
