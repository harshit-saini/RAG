from __future__ import annotations

from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorClient

from app.config import Settings


class MongoStorage:
    def __init__(self, settings: Settings):
        self.client = AsyncIOMotorClient(settings.mongo_uri)
        self.db = self.client[settings.mongo_db]
        self.docs = self.db[settings.mongo_collection_docs]
        self.chunks = self.db[settings.mongo_collection_chunks]

    async def ensure_indexes(self) -> None:
        await self.docs.create_index("document_id", unique=True)
        await self.chunks.create_index("chunk_id", unique=True)
        await self.chunks.create_index("document_id")

    async def upsert_document(self, document: dict) -> None:
        payload = {
            **document,
            "updated_at": datetime.now(timezone.utc),
        }
        await self.docs.update_one(
            {"document_id": document["document_id"]},
            {"$set": payload, "$setOnInsert": {"created_at": datetime.now(timezone.utc)}},
            upsert=True,
        )

    async def replace_document_chunks(self, document_id: str, chunks: list[dict]) -> None:
        await self.chunks.delete_many({"document_id": document_id})
        if chunks:
            await self.chunks.insert_many(chunks)

    async def get_chunks_by_ids(self, chunk_ids: list[str]) -> list[dict]:
        if not chunk_ids:
            return []
        cursor = self.chunks.find({"chunk_id": {"$in": chunk_ids}})
        rows = await cursor.to_list(length=len(chunk_ids))
        row_map = {row["chunk_id"]: row for row in rows}
        return [row_map[cid] for cid in chunk_ids if cid in row_map]
