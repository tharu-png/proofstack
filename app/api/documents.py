
from fastapi import APIRouter, File, HTTPException, UploadFile
from app.services.document_storage import save_pdf
from app.services.pdf_extractor import extract_pdf_pages


router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/extract")
async def extract_document(file: UploadFile = File(...)):
    """Upload a PDF and return its extracted page text."""

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
        raise HTTPException(status_code=400, detail=str(exc))

    stored_filename = save_pdf(pdf_bytes)

    return {
        "filename": file.filename,
        "page_count": len(pages),
        "stored_filename": stored_filename,
        "pages": pages,
    }
