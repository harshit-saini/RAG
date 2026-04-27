from __future__ import annotations


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 150) -> list[str]:
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be larger than overlap")

    normalized = " ".join(text.split())
    chunks: list[str] = []
    start = 0

    while start < len(normalized):
        end = min(start + chunk_size, len(normalized))
        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(normalized):
            break
        start = end - overlap

    return chunks
