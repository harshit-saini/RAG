from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException

from app.config import Settings, get_settings
from app.models.schemas import (
    DocumentIn,
    IngestResponse,
    QueryRequest,
    QueryResponse,
    RetrievedChunk,
)
from app.services.chunker import chunk_text
from app.services.generator import LLMGenerator
from app.services.retriever import OpenSearchRetriever
from app.services.storage import MongoStorage

app = FastAPI(title="Vectorless RAG Backend", version="0.1.0")


@app.on_event("startup")
async def startup() -> None:
    settings = get_settings()
    storage = MongoStorage(settings)
    retriever = OpenSearchRetriever(settings)

    await storage.ensure_indexes()
    retriever.ensure_index()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/v1/documents", response_model=IngestResponse)
async def ingest_document(document: DocumentIn, settings: Settings = Depends(get_settings)) -> IngestResponse:
    chunks = chunk_text(
        document.text,
        chunk_size=settings.chunk_size_chars,
        overlap=settings.chunk_overlap_chars,
    )

    chunk_docs = [
        {
            "chunk_id": f"{document.document_id}:{i}",
            "document_id": document.document_id,
            "title": document.title,
            "text": text,
            "metadata": document.metadata,
        }
        for i, text in enumerate(chunks)
    ]

    storage = MongoStorage(settings)
    retriever = OpenSearchRetriever(settings)

    await storage.upsert_document(document.model_dump())
    await storage.replace_document_chunks(document.document_id, chunk_docs)
    retriever.replace_document_chunks(document.document_id, chunk_docs)

    return IngestResponse(document_id=document.document_id, chunks_indexed=len(chunk_docs))


@app.post("/v1/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest, settings: Settings = Depends(get_settings)) -> QueryResponse:
    retriever = OpenSearchRetriever(settings)
    storage = MongoStorage(settings)
    generator = LLMGenerator(settings)

    hits = retriever.search(request.query, request.top_k or settings.top_k_retrieval)
    if not hits:
        raise HTTPException(status_code=404, detail="No relevant chunks found")

    ordered_chunk_ids = [hit["chunk_id"] for hit in hits]
    chunks = await storage.get_chunks_by_ids(ordered_chunk_ids)
    if not chunks:
        raise HTTPException(status_code=404, detail="Chunks referenced by index are missing")

    score_map = {hit["chunk_id"]: hit["score"] for hit in hits}
    enriched = []
    for chunk in chunks:
        enriched.append(
            RetrievedChunk(
                chunk_id=chunk["chunk_id"],
                document_id=chunk["document_id"],
                title=chunk["title"],
                text=chunk["text"],
                metadata=chunk.get("metadata", {}),
                score=score_map.get(chunk["chunk_id"], 0.0),
            )
        )

    answer = await generator.answer(request.query, [c.model_dump() for c in enriched])
    citations = sorted({chunk.document_id for chunk in enriched})

    return QueryResponse(answer=answer, citations=citations, chunks=enriched)
