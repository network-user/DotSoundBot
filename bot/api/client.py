from typing import Any

import httpx
import structlog

from bot.config import settings

logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)


class BackendError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Backend error {status_code}: {detail}")


class BackendClient:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=settings.backend_base_url,
            timeout=30.0,
        )

    async def get(self, path: str, **kwargs: Any) -> Any:
        logger.debug("backend_get", path=path)
        response = await self._client.get(path, **kwargs)
        self._raise_for_status(response)
        return response.json()

    async def post(self, path: str, **kwargs: Any) -> Any:
        logger.debug("backend_post", path=path)
        response = await self._client.post(path, **kwargs)
        self._raise_for_status(response)
        return response.json()

    async def upload_audio(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        title: str,
        artist: str | None = None,
        uploader_id: int | None = None,
    ) -> dict[str, Any]:
        """Upload audio file as multipart/form-data."""
        logger.info(
            "backend_upload_audio",
            filename=filename,
            size_bytes=len(file_bytes),
            title=title,
        )
        files = {
            "file": (filename, file_bytes, content_type),
        }
        data: dict[str, Any] = {"title": title}
        if artist:
            data["artist"] = artist
        if uploader_id is not None:
            data["uploader_id"] = str(uploader_id)

        response = await self._client.post(
            "/api/v1/tracks/upload",
            files=files,
            data=data,
        )
        self._raise_for_status(response)
        result: dict[str, Any] = response.json()
        logger.info(
            "backend_upload_complete",
            track_id=result.get("id"),
        )
        return result

    async def get_user_stats(
        self, user_id: int
    ) -> dict[str, Any]:
        logger.info("backend_get_user_stats", user_id=user_id)
        return await self.get(f"/api/v1/users/{user_id}/stats")

    async def get_user_profile(
        self, telegram_id: int
    ) -> dict[str, Any]:
        logger.info(
            "backend_get_user_profile", telegram_id=telegram_id
        )
        return await self.get(f"/api/v1/users/{telegram_id}")

    async def get_user_playlists(
        self, owner_id: int
    ) -> list[dict[str, Any]]:
        logger.info(
            "backend_get_user_playlists", owner_id=owner_id
        )
        result = await self.get(
            "/api/v1/playlists",
            params={"owner_id": owner_id},
        )
        return result if isinstance(result, list) else []

    async def create_playlist(
        self, owner_id: int, name: str, is_public: bool = False
    ) -> dict[str, Any]:
        logger.info(
            "backend_create_playlist",
            owner_id=owner_id,
            name=name,
        )
        response = await self._client.post(
            "/api/v1/playlists",
            params={"owner_id": owner_id},
            json={"name": name, "is_public": is_public},
        )
        self._raise_for_status(response)
        result: dict[str, Any] = response.json()
        logger.info(
            "backend_playlist_created",
            playlist_id=result.get("id"),
        )
        return result

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "BackendClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.is_error:
            logger.warning(
                "backend_error_response",
                status_code=response.status_code,
                path=str(response.url),
            )
            raise BackendError(response.status_code, response.text)
