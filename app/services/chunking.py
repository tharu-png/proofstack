
from typing import Dict, List


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 150,
) -> List[Dict[str, object]]:
    """Split text into overlapping character-based chunks."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive.")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size.")

    chunks = []
    start = 0
    chunk_index = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()

        if chunk:
            chunks.append({
                "chunk_index": chunk_index,
                "text": chunk,
            })
            chunk_index += 1

        if end == len(text):
            break

        start = end - overlap

    return chunks
