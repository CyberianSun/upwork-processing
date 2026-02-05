import asyncio
import httpx
from typing import Any, TypeVar, Dict
from pydantic import BaseModel

from core.config import settings

T = TypeVar("T", bound=BaseModel)


class CerebrasClient:
    """Cerebras GLM 4.7 API client with rate limiting.

    Handles chat completions with automatic retry logic and respect for API limits.
    """

    def __init__(self):
        """Initialize client with rate limiting settings from config."""
        self.api_key = settings.cerebras_api_key
        self.model = settings.cerebras_model
        self.base_url = "https://api.cerebras.ai/v1"
        self._http_client: httpx.AsyncClient | None = None

        self._semaphore = asyncio.Semaphore(settings.rate_limit_concurrent)
        self._request_lock = asyncio.Lock()
        self._min_request_interval = 1.0 / settings.rate_limit_requests
        self._last_request_time = 0.0
        self._loop = asyncio.get_event_loop()

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with authorization header."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=settings.api_timeout,
            )
        return self._http_client

    async def _rate_limit(self):
        """Enforce rate limiting between API requests."""
        async with self._request_lock:
            elapsed = self._loop.time() - self._last_request_time
            if elapsed < self._min_request_interval:
                await asyncio.sleep(self._min_request_interval - elapsed)
            self._last_request_time = self._loop.time()

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        response_model: type[T],
    ) -> T:
        """Send chat completion request with retry logic.

        Args:
            messages: Chat messages for the model
            response_model: Pydantic type to validate response

        Returns:
            Validated response matching response_model

        Raises:
            Exception: After 3 retry attempts
        """
        import json

        async with self._semaphore:
            await self._rate_limit()
            client = await self._get_client()

            for attempt in range(3):
                try:
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

                    if isinstance(content, str):
                        parsed = json.loads(content)
                    else:
                        parsed = content

                    return response_model.model_validate(parsed)
                except Exception as e:
                    if attempt == 2:
                        raise
                    await asyncio.sleep(2 ** attempt)

    async def close(self):
        """Close HTTP client connection."""
        if self._http_client:
            await self._http_client.aclose()