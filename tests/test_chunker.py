from app.services.chunker import chunk_text


def test_chunk_text_has_overlap_and_multiple_chunks() -> None:
    text = "A" * 2500
    chunks = chunk_text(text, chunk_size=1000, overlap=100)

    assert len(chunks) == 3
    assert len(chunks[0]) == 1000
    assert len(chunks[1]) == 1000


def test_chunk_text_validates_sizes() -> None:
    try:
        chunk_text("hello", chunk_size=100, overlap=100)
        assert False, "Expected ValueError"
    except ValueError:
        assert True
