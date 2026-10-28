
from fastapi import APIRouter, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import engine
from app.models import Document, DocumentChunk, DocumentPage
from app.services.document_storage import save_pdf
from app.services.pdf_extractor import extract_pdf_pages
from app.services.chunking import chunk_text

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/extract")
async def extract_document(file: UploadFile = File(...)):
    """Upload a PDF, extract its text, and save its metadata."""

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported.",
        )

    pdf_bytes = await file.read()

    if not pdf_bytes:
        raise HTTPException(
            status_code=400,
            detail="The uploaded PDF file is empty.",
        )

    try:
        pages = extract_pdf_pages(pdf_bytes)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    stored_filename = save_pdf(pdf_bytes)

    with Session(engine) as session:
        document = Document(
            original_filename=file.filename or "unnamed.pdf",
            stored_filename=stored_filename,
            page_count=len(pages),
        )

        session.add(document)
        session.flush()

        for page in pages:
            document_page = DocumentPage(
                document_id=document.id,
                page_number=page["page_number"],
                text=page["text"],
            )
            session.add(document_page)

            chunks = chunk_text(page["text"])

            for chunk in chunks:
                document_chunk = DocumentChunk(
                    document_id=document.id,
                    page_number=page["page_number"],
                    chunk_index=chunk["chunk_index"],
                    text=chunk["text"],
                )
                session.add(document_chunk)

        session.commit()
        session.refresh(document)

        document_id = str(document.id)
        uploaded_at = document.uploaded_at.isoformat()

    return {
        "document_id": document_id,
        "filename": file.filename,
        "page_count": len(pages),
        "stored_filename": stored_filename,
        "uploaded_at": uploaded_at,
        "pages": pages,
    }


@router.get("/")
def list_documents():
    """Return all documents saved in the database."""

    with Session(engine) as session:
        documents = (
            session.query(Document)
            .order_by(Document.uploaded_at.desc())
            .all()
        )

        return [
            {
                "document_id": str(document.id),
                "filename": document.original_filename,
                "stored_filename": document.stored_filename,
                "page_count": document.page_count,
                "uploaded_at": document.uploaded_at.isoformat(),
            }
            for document in documents
        ]


@router.get("/{document_id}/pages")
def get_document_pages(document_id: str):
    """Return the extracted text for each page of a document."""

    with Session(engine) as session:
        document = session.get(Document, document_id)

        if document is None:
            raise HTTPException(
                status_code=404,
                detail="Document not found.",
            )

        pages = (
            session.query(DocumentPage)
            .filter(DocumentPage.document_id == document.id)
            .order_by(DocumentPage.page_number)
            .all()
        )

        return [
            {
                "page_number": page.page_number,
                "text": page.text,
            }
            for page in pages
        ]
