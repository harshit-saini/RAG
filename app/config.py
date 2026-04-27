from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Vectorless RAG API"
    env: str = "dev"

    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "rag"
    mongo_collection_docs: str = "documents"
    mongo_collection_chunks: str = "chunks"

    opensearch_host: str = "http://localhost:9200"
    opensearch_index: str = "rag_chunks"
    opensearch_user: str | None = None
    opensearch_password: str | None = None
    opensearch_verify_certs: bool = False

    chunk_size_chars: int = 1200
    chunk_overlap_chars: int = 150
    top_k_retrieval: int = 8

    llm_provider: str = "openai"
    llm_model: str = "gpt-4.1-mini"
    llm_api_key: str | None = None
    llm_base_url: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
