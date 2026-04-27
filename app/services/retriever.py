from __future__ import annotations

from opensearchpy import OpenSearch

from app.config import Settings


class OpenSearchRetriever:
    def __init__(self, settings: Settings):
        auth = None
        if settings.opensearch_user and settings.opensearch_password:
            auth = (settings.opensearch_user, settings.opensearch_password)

        self.index = settings.opensearch_index
        self.client = OpenSearch(
            hosts=[settings.opensearch_host],
            http_auth=auth,
            use_ssl=settings.opensearch_host.startswith("https://"),
            verify_certs=settings.opensearch_verify_certs,
            ssl_assert_hostname=False,
            ssl_show_warn=False,
        )

    def ensure_index(self) -> None:
        if self.client.indices.exists(index=self.index):
            return

        body = {
            "settings": {"index": {"number_of_shards": 1, "number_of_replicas": 1}},
            "mappings": {
                "properties": {
                    "chunk_id": {"type": "keyword"},
                    "document_id": {"type": "keyword"},
                    "title": {"type": "text"},
                    "text": {"type": "text"},
                    "metadata": {"type": "object", "enabled": True},
                }
            },
        }
        self.client.indices.create(index=self.index, body=body)

    def replace_document_chunks(self, document_id: str, chunks: list[dict]) -> None:
        self.client.delete_by_query(
            index=self.index,
            body={"query": {"term": {"document_id": document_id}}},
            conflicts="proceed",
            refresh=True,
        )
        if not chunks:
            return

        operations = []
        for chunk in chunks:
            operations.append({"index": {"_index": self.index, "_id": chunk["chunk_id"]}})
            operations.append(chunk)

        self.client.bulk(body=operations, refresh=True)

    def search(self, query: str, top_k: int) -> list[dict]:
        body = {
            "size": top_k,
            "query": {
                "bool": {
                    "should": [
                        {"match": {"text": {"query": query, "boost": 2.0}}},
                        {"match": {"title": {"query": query, "boost": 1.2}}},
                    ]
                }
            },
        }
        response = self.client.search(index=self.index, body=body)
        return [
            {
                "chunk_id": hit["_source"]["chunk_id"],
                "score": float(hit["_score"]),
            }
            for hit in response["hits"]["hits"]
        ]
