from typing import Any

import httpx

from bot.config import settings


class BackendError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Backend error {status_code}: {detail}")


class BackendClient:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=settings.backend_base_url,
            timeout=10.0,
        )

    async def get(
        self,
        path: str,
        **kwargs: Any,
    ) -> Any:
        response = await self._client.get(path, **kwargs)
        self._raise_for_status(response)
        return response.json()

    async def post(
        self,
        path: str,
        **kwargs: Any,
    ) -> Any:
        response = await self._client.post(path, **kwargs)
        self._raise_for_status(response)
        return response.json()

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "BackendClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.is_error:
            detail = response.text
            raise BackendError(response.status_code, detail)
