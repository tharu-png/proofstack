
import pytest

from app.services.chunking import chunk_text


def test_short_text_returns_one_chunk():
    chunks = chunk_text("ProofStack evidence test.")

    assert len(chunks) == 1
    assert chunks[0]["chunk_index"] == 0
    assert chunks[0]["text"] == "ProofStack evidence test."


def test_long_text_is_split_with_overlap():
    chunks = chunk_text(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        chunk_size=10,
        overlap=3,
    )

    assert len(chunks) == 4
    assert chunks[0]["text"] == "ABCDEFGHIJ"
    assert chunks[1]["text"] == "HIJKLMNOPQ"
    assert chunks[2]["text"] == "OPQRSTUVWX"
    assert chunks[3]["text"] == "VWXYZ"


def test_chunk_indexes_start_at_zero():
    chunks = chunk_text(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        chunk_size=10,
        overlap=3,
    )

    assert [chunk["chunk_index"] for chunk in chunks] == [0, 1, 2, 3]


def test_zero_chunk_size_is_rejected():
    with pytest.raises(ValueError, match="chunk_size must be positive"):
        chunk_text("hello", chunk_size=0)


def test_overlap_equal_to_chunk_size_is_rejected():
    with pytest.raises(
        ValueError,
        match="overlap must be non-negative and smaller than chunk_size",
    ):
        chunk_text("hello", chunk_size=10, overlap=10)


def test_negative_overlap_is_rejected():
    with pytest.raises(
        ValueError,
        match="overlap must be non-negative and smaller than chunk_size",
    ):
        chunk_text("hello", chunk_size=10, overlap=-1)


def test_empty_text_returns_no_chunks():
    assert chunk_text("") == []


def test_whitespace_only_text_returns_no_chunks():
    assert chunk_text("   \n   ") == []
