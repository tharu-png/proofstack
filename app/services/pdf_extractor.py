
import fitz
from typing import Dict, List, Union



def extract_pdf_pages(pdf_bytes: bytes) -> List[Dict[str, Union[int, str]]]:
    """Extract text from a PDF while preserving page numbers."""

    try:
        document = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise ValueError("Could not read a valid PDF file.") from exc

    try:
        if document.is_encrypted:
            raise ValueError(
                "Password-protected PDFs are not supported yet."
            )

        pages = []

        for page_index, page in enumerate(document):
            pages.append(
                {
                    "page_number": page_index + 1,
                    "text": page.get_text("text").strip(),
                }
            )

        return pages
    finally:
        document.close()
