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
            timeout=5.0,
        )

    async def get(self, path: str, **kwargs: Any) -> Any:
        logger.debug("backend_get", path=path)
        response = await self._request("GET", path, **kwargs)
        return response.json()

    async def post(self, path: str, **kwargs: Any) -> Any:
        logger.debug("backend_post", path=path)
        response = await self._request("POST", path, **kwargs)
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

        response = await self._request(
            "POST",
            "/api/v1/tracks/upload",
            files=files,
            data=data,
            timeout=60.0,
        )
        result: dict[str, Any] = response.json()
        logger.info(
            "backend_upload_complete",
            track_id=result.get("id"),
        )
        return result

    async def toggle_like(
        self, user_id: int, track_id: int
    ) -> dict[str, Any]:
        logger.info(
            "backend_toggle_like",
            user_id=user_id,
            track_id=track_id,
        )
        return await self.post(
            f"/api/v1/likes/{user_id}/{track_id}"
        )

    async def toggle_dislike(
        self, user_id: int, track_id: int
    ) -> dict[str, Any]:
        logger.info(
            "backend_toggle_dislike",
            user_id=user_id,
            track_id=track_id,
        )
        return await self.post(
            f"/api/v1/dislikes/{user_id}/{track_id}"
        )

    async def get_user_profile(
        self, telegram_id: int
    ) -> dict[str, Any]:
        logger.info(
            "backend_get_user_profile",
            telegram_id=telegram_id,
        )
        return await self.get(f"/api/v1/users/{telegram_id}")

    async def get_user_stats(
        self, user_id: int
    ) -> dict[str, Any]:
        logger.info(
            "backend_get_user_stats", user_id=user_id
        )
        return await self.get(
            f"/api/v1/users/{user_id}/stats"
        )

    async def get_login_history(
        self, user_id: int
    ) -> list[dict[str, Any]]:
        logger.info(
            "backend_get_login_history",
            user_id=user_id,
        )
        result = await self.get(
            f"/api/v1/users/{user_id}/login-history"
        )
        return (
            result if isinstance(result, list) else []
        )

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
        self,
        owner_id: int,
        name: str,
        is_public: bool = False,
    ) -> dict[str, Any]:
        logger.info(
            "backend_create_playlist",
            owner_id=owner_id,
            name=name,
        )
        response = await self._request(
            "POST",
            "/api/v1/playlists",
            params={"owner_id": owner_id},
            json={"name": name, "is_public": is_public},
        )
        result: dict[str, Any] = response.json()
        logger.info(
            "backend_playlist_created",
            playlist_id=result.get("id"),
        )
        return result

    async def get_internal_token(
        self,
        telegram_id: int,
        secret: str,
    ) -> dict[str, Any]:
        from dotsound_private_core.contracts import (
            INTERNAL_SECRET_HEADER,
        )

        response = await self._request(
            "POST",
            "/api/v1/auth/internal-token",
            json={"telegram_id": telegram_id},
            headers={INTERNAL_SECRET_HEADER: secret},
        )
        return response.json()

    async def get_stream_url(
        self, track_id: int, token: str
    ) -> str:
        response = await self._request(
            "GET",
            f"/api/v1/tracks/{track_id}/stream",
            headers={
                "Authorization": f"Bearer {token}"
            },
        )
        data: dict[str, Any] = response.json()
        return str(data["url"])

    async def get_my_tracks(
        self,
        token: str,
        page: int = 1,
        size: int = 3,
    ) -> dict[str, Any]:
        response = await self._request(
            "GET",
            "/api/v1/tracks/my",
            params={"page": page, "size": size},
            headers={
                "Authorization": f"Bearer {token}"
            },
        )
        return response.json()

    async def get_liked_tracks(
        self,
        user_id: int,
        token: str,
        size: int = 200,
    ) -> dict[str, Any]:
        response = await self._request(
            "GET",
            f"/api/v1/likes/{user_id}",
            params={"size": size},
            headers={
                "Authorization": f"Bearer {token}"
            },
        )
        return response.json()

    async def get_feed_tracks(
        self,
        page: int = 1,
        size: int = 3,
    ) -> dict[str, Any]:
        return await self.get(
            "/api/v1/tracks",
            params={"page": page, "size": size},
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "BackendClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    async def _request(
        self, method: str, path: str, **kwargs: Any
    ) -> httpx.Response:
        try:
            response = await self._client.request(
                method, path, **kwargs
            )
            self._raise_for_status(response)
            return response
        except httpx.TimeoutException:
            logger.error(
                "backend_timeout", method=method, path=path
            )
            raise BackendError(
                504, "Backend read/connect timeout"
            )
        except httpx.NetworkError:
            logger.error(
                "backend_network_error",
                method=method,
                path=path,
            )
            raise BackendError(
                502, "Backend connection error"
            )
        except httpx.HTTPError as exc:
            logger.error(
                "backend_http_error",
                method=method,
                path=path,
                exc=str(exc),
            )
            raise BackendError(
                500, f"Backend HTTP error: {str(exc)}"
            )

    def _raise_for_status(
        self, response: httpx.Response
    ) -> None:
        if response.is_error:
            logger.warning(
                "backend_error_response",
                status_code=response.status_code,
                path=str(response.url),
            )
            raise BackendError(
                response.status_code, response.text
            )
