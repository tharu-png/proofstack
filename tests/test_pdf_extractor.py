
import fitz
import pytest

import uuid

from sqlalchemy.orm import Session
from app.database import engine
from app.models import Document

from app.services.pdf_extractor import extract_pdf_pages
from fastapi.testclient import TestClient
from app.main import app

from pathlib import Path
from app.services.document_storage import UPLOAD_DIR

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

def test_rejects_empty_pdf_upload():
    client = TestClient(app)

    response = client.post(
        "/documents/extract",
        files={
            "file": (
                "empty.pdf",
                b"",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "The uploaded PDF file is empty."


def test_upload_pdf_saves_original_file():
    pdf_bytes = create_test_pdf()
    client = TestClient(app)

    response = client.post(
        "/documents/extract",
        files={
            "file": (
                "storage_test.pdf",
                pdf_bytes,
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()
    stored_filename = data["stored_filename"]
    stored_path = UPLOAD_DIR / stored_filename

    assert stored_path.exists()
    assert stored_path.read_bytes() == pdf_bytes

    document_id = uuid.UUID(data["document_id"])

    with Session(engine) as session:
        saved_document = session.get(Document, document_id)

        assert saved_document is not None
        assert saved_document.original_filename == "storage_test.pdf"
        assert saved_document.stored_filename == data["stored_filename"]
        assert saved_document.page_count == 2
        assert saved_document.uploaded_at is not None


def test_list_documents():
    client = TestClient(app)

    response = client.get("/documents/")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    if data:
        document = data[0]

        assert "document_id" in document
        assert "filename" in document
        assert "stored_filename" in document
        assert "page_count" in document
        assert "uploaded_at" in document


def test_get_document_pages_not_found():
    client = TestClient(app)

    response = client.get(
        "/documents/00000000-0000-0000-0000-000000000000/pages"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found."




def test_get_document_pages_returns_saved_text():
    client = TestClient(app)

    # Create a PDF containing two known pages.
    pdf_bytes = create_test_pdf()

    # Upload the PDF through the API.
    upload_response = client.post(
        "/documents/extract",
        files={
            "file": (
                "retrieval_test.pdf",
                pdf_bytes,
                "application/pdf",
            )
        },
    )

    assert upload_response.status_code == 200

    document_id = upload_response.json()["document_id"]

    # Retrieve the saved page text.
    response = client.get(
        "/documents/{}/pages".format(document_id)
    )

    assert response.status_code == 200

    pages = response.json()

    assert len(pages) == 2
    assert pages[0]["page_number"] == 1
    assert pages[0]["text"] == "ProofStack evidence on page one."
    assert pages[1]["page_number"] == 2
    assert pages[1]["text"] == "ProofStack evidence on page two."
