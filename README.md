# Vectorless RAG Backend (FastAPI + MongoDB Atlas + AWS OpenSearch)

This project provides a **Python FastAPI backend** for Retrieval-Augmented Generation (RAG) at 1k+ document scale without requiring vector embeddings.

## Why vectorless RAG?

Instead of vector DB search, this backend uses lexical retrieval (BM25 in OpenSearch) with:
- chunked documents in MongoDB Atlas
- indexed chunks in AWS OpenSearch Service
- LLM generation over retrieved passages

This is often cheaper to start, easier to inspect, and performs well when documents are structured or domain-specific.

## Architecture

1. **Ingestion** (`POST /v1/documents`)
   - Document is chunked.
   - Full metadata and chunks saved to MongoDB Atlas.
   - Chunks indexed in OpenSearch.

2. **Query** (`POST /v1/query`)
   - Query sent to OpenSearch lexical search.
   - Top chunks fetched from MongoDB.
   - Context passed to LLM for answer synthesis.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
```

Run API:

```bash
uvicorn app.main:app --reload --port 8000
```

## API examples

### Ingest

```bash
curl -X POST http://localhost:8000/v1/documents \
  -H "content-type: application/json" \
  -d '{
    "document_id": "handbook-001",
    "title": "Employee Handbook",
    "text": "Long document text here ...",
    "metadata": {"source": "hr", "version": "2026.1"}
  }'
```

### Query

```bash
curl -X POST http://localhost:8000/v1/query \
  -H "content-type: application/json" \
  -d '{"query": "What is the PTO policy?", "top_k": 6}'
```

## Scaling notes for 1,000+ docs

- Use AWS OpenSearch with multi-AZ and tune shards/replicas.
- Keep chunks around 800–1500 chars with overlap.
- Add filters on `metadata` in retrieval queries for tenant/domain scoping.
- Add reranking (cross-encoder / LLM rerank) when precision matters.
- Consider hybrid fallback with Amazon Kendra or Bedrock Knowledge Bases later.

## Optional integrations

- **Google LangExtract** or custom extraction pipeline can be added before chunking for cleaner sections.
- OCR (Textract) for PDFs/images before ingestion.
- S3 event-driven ingestion using Lambda + SQS.

## Notes

- If `LLM_API_KEY` is missing, the API returns a context preview fallback instead of an LLM answer.
- This repo intentionally keeps retrieval **vectorless**; embeddings can be added as a second-stage enhancement.
