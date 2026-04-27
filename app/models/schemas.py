from pydantic import BaseModel, Field


class DocumentIn(BaseModel):
    document_id: str = Field(..., description="Unique ID for the source document")
    title: str
    text: str = Field(..., min_length=30)
    metadata: dict = Field(default_factory=dict)


class IngestResponse(BaseModel):
    document_id: str
    chunks_indexed: int


class QueryRequest(BaseModel):
    query: str
    top_k: int = 8


class RetrievedChunk(BaseModel):
    chunk_id: str
    document_id: str
    title: str
    text: str
    score: float
    metadata: dict = Field(default_factory=dict)


class QueryResponse(BaseModel):
    answer: str
    citations: list[str]
    chunks: list[RetrievedChunk]
