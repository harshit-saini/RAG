from __future__ import annotations

import httpx

from app.config import Settings


class LLMGenerator:
    def __init__(self, settings: Settings):
        self.provider = settings.llm_provider
        self.model = settings.llm_model
        self.api_key = settings.llm_api_key
        self.base_url = settings.llm_base_url or "https://api.openai.com/v1"

    async def answer(self, query: str, contexts: list[dict]) -> str:
        if not self.api_key:
            context_preview = "\n\n".join([c["text"][:400] for c in contexts[:3]])
            return (
                "LLM_API_KEY is not configured. Retrieved context preview:\n"
                f"{context_preview}\n\nQuestion: {query}"
            )

        prompt_context = "\n\n".join(
            [f"[doc:{c['document_id']}] {c['text']}" for c in contexts]
        )
        system = (
            "You are a RAG assistant. Answer only using retrieved passages. "
            "If uncertain, say you do not know."
        )
        user = f"Question: {query}\n\nRetrieved Passages:\n{prompt_context}"

        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": 0.1,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
