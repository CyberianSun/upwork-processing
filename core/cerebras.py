import asyncio
import httpx
from typing import Any, TypeVar
from pydantic import BaseModel

from core.config import settings

T = TypeVar("T", bound=BaseModel)


class CerebrasClient:
    def __init__(self):
        self.api_key = settings.cerebras_api_key
        self.model = settings.cerebras_model
        self.base_url = "https://api.cerebras.ai/v1"
        self._client: httpx.AsyncClient | None = None

        self._semaphore = asyncio.Semaphore(settings.rate_limit_concurrent)
        self._request_lock = asyncio.Lock()
        self._min_request_interval = 1.0 / settings.rate_limit_requests
        self._last_request_time = 0.0

    async def _client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=settings.api_timeout,
            )
        return self._client

    async def _rate_limit(self):
        async with self._request_lock:
            elapsed = asyncio.get_event_loop().time() - self._last_request_time
            if elapsed < self._min_request_interval:
                await asyncio.sleep(self._min_request_interval - elapsed)
            self._last_request_time = asyncio.get_event_loop().time()

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        response_model: type[T],
    ) -> T:
        async with self._semaphore:
            await self._rate_limit()
            client = await self._client()

            response = await client.post(
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "response_format": {"type": "json_object"},
                    "temperature": 0.1,
                },
            )

            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]

            return response_model.model_validate_json(content)

    async def close(self):
        if self._client:
            await self._client.aclose()