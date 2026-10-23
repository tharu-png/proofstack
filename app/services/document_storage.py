
from pathlib import Path
from uuid import uuid4


UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"


def save_pdf(pdf_bytes: bytes) -> str:
    """Save a PDF and return its unique stored filename."""

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    stored_filename = "{}.pdf".format(uuid4().hex)
    file_path = UPLOAD_DIR / stored_filename

    file_path.write_bytes(pdf_bytes)

    return stored_filename
