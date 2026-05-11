import asyncio
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

    async def _get_token_for_user(
        self, telegram_id: int
    ) -> str:
        secret = settings.internal_api_secret
        if not secret:
            raise BackendError(
                500, "internal_api_secret not configured"
            )
        result = await self.get_internal_token(
            telegram_id, secret
        )
        return str(result["access_token"])

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

        headers: dict[str, str] = {}
        if uploader_id is not None:
            try:
                token = await self._get_token_for_user(
                    uploader_id
                )
                headers["Authorization"] = (
                    f"Bearer {token}"
                )
            except Exception:
                logger.warning("upload_token_failed")

        response = await self._request(
            "POST",
            "/api/v1/tracks/upload",
            files=files,
            data=data,
            headers=headers,
            timeout=60.0,
        )
        result: dict[str, Any] = response.json()
        logger.info(
            "backend_upload_complete",
            track_id=result.get("id"),
        )
        return result

    async def toggle_like(
        self,
        user_id: int,
        track_id: int,
        token: str,
    ) -> dict[str, Any]:
        logger.info(
            "backend_toggle_like",
            user_id=user_id,
            track_id=track_id,
        )
        response = await self._request(
            "POST",
            f"/api/v1/likes/{user_id}/{track_id}",
            headers={
                "Authorization": f"Bearer {token}"
            },
        )
        result: dict[str, Any] = response.json()
        return result

    async def toggle_dislike(
        self,
        user_id: int,
        track_id: int,
        token: str,
    ) -> dict[str, Any]:
        logger.info(
            "backend_toggle_dislike",
            user_id=user_id,
            track_id=track_id,
        )
        response = await self._request(
            "POST",
            f"/api/v1/dislikes/{user_id}/{track_id}",
            headers={
                "Authorization": f"Bearer {token}"
            },
        )
        result: dict[str, Any] = response.json()
        return result

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
        self, owner_id: int, telegram_id: int = 0
    ) -> list[dict[str, Any]]:
        logger.info(
            "backend_get_user_playlists",
            owner_id=owner_id,
        )
        headers: dict[str, str] = {}
        tg_id = telegram_id or owner_id
        try:
            token = await self._get_token_for_user(
                tg_id
            )
            headers["Authorization"] = (
                f"Bearer {token}"
            )
        except Exception:
            logger.warning("playlist_list_token_failed")
        response = await self._request(
            "GET",
            "/api/v1/playlists",
            headers=headers,
        )
        result = response.json()
        return (
            result if isinstance(result, list) else []
        )

    async def create_playlist(
        self,
        owner_id: int,
        name: str,
        is_public: bool = False,
        telegram_id: int = 0,
    ) -> dict[str, Any]:
        logger.info(
            "backend_create_playlist",
            owner_id=owner_id,
            name=name,
        )
        headers: dict[str, str] = {}
        tg_id = telegram_id or owner_id
        try:
            token = await self._get_token_for_user(
                tg_id
            )
            headers["Authorization"] = (
                f"Bearer {token}"
            )
        except Exception:
            logger.warning("playlist_create_token_failed")
        response = await self._request(
            "POST",
            "/api/v1/playlists",
            json={
                "name": name,
                "is_public": is_public,
            },
            headers=headers,
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
        playable: bool = False,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "page": page,
            "size": size,
        }
        if playable:
            params["playable"] = "true"
        response = await self._request(
            "GET",
            "/api/v1/tracks/my",
            params=params,
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
        playable: bool = False,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "page": page,
            "size": size,
        }
        if playable:
            params["playable"] = "true"
        return await self.get(
            "/api/v1/tracks",
            params=params,
        )

    async def get_followed_artists_tracks(
        self,
        token: str,
        page: int = 1,
        size: int = 3,
        playable: bool = False,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "page": page,
            "size": size,
        }
        if playable:
            params["playable_only"] = "true"
        response = await self._request(
            "GET",
            "/api/v1/users/me/followed-artists/tracks",
            params=params,
            headers={
                "Authorization": f"Bearer {token}"
            },
        )
        return response.json()

    @staticmethod
    def _is_playable_track(track: dict[str, Any]) -> bool:
        return bool(
            track.get("source") == "soundcloud"
            or track.get("processing_status") == "active"
        )

    @staticmethod
    def _page_items(
        items: list[dict[str, Any]], page: int, size: int
    ) -> dict[str, Any]:
        total = len(items)
        start = max(0, (page - 1) * size)
        end = start + size
        return {"items": items[start:end], "total": total}

    async def get_recommendation_tracks(
        self,
        token: str,
        page: int = 1,
        size: int = 3,
        playable: bool = False,
    ) -> dict[str, Any]:
        response = await self._request(
            "GET",
            "/api/v1/recommendations/daily-playlist",
            headers={
                "Authorization": f"Bearer {token}"
            },
        )
        data: dict[str, Any] = response.json()
        combined: list[dict[str, Any]] = []
        seen: set[int] = set()
        groups = (
            data.get("internal_tracks", []),
            data.get("global_top", []),
            data.get("external_tracks", []),
        )
        for group in groups:
            if not isinstance(group, list):
                continue
            for track in group:
                if not isinstance(track, dict):
                    continue
                track_id = track.get("id")
                if not isinstance(track_id, int):
                    continue
                if track_id in seen:
                    continue
                if playable and not self._is_playable_track(track):
                    continue
                seen.add(track_id)
                combined.append(track)
        return self._page_items(combined, page, size)

    async def get_playlist_source_tracks(
        self,
        token: str,
        page: int = 1,
        size: int = 3,
        playable: bool = False,
    ) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {token}"}
        playlists_resp = await self._request(
            "GET",
            "/api/v1/playlists",
            headers=headers,
        )
        playlists_data = playlists_resp.json()
        if not isinstance(playlists_data, list):
            return {"items": [], "total": 0}
        playlists: list[dict[str, Any]] = [
            item for item in playlists_data if isinstance(item, dict)
        ]

        playlist_ids = [
            playlist.get("id")
            for playlist in playlists
            if isinstance(playlist.get("id"), int)
        ]
        if not playlist_ids:
            return {"items": [], "total": 0}

        details = await asyncio.gather(
            *(
                self._request(
                    "GET",
                    f"/api/v1/playlists/{pid}",
                    headers=headers,
                )
                for pid in playlist_ids
            ),
            return_exceptions=True,
        )

        tracks: list[dict[str, Any]] = []
        seen: set[int] = set()
        for detail in details:
            if isinstance(detail, BaseException):
                continue
            payload = detail.json()
            pl_tracks = payload.get("tracks", [])
            if not isinstance(pl_tracks, list):
                continue
            for track in pl_tracks:
                if not isinstance(track, dict):
                    continue
                track_id = track.get("id")
                if not isinstance(track_id, int):
                    continue
                if track_id in seen:
                    continue
                if playable and not self._is_playable_track(track):
                    continue
                seen.add(track_id)
                tracks.append(track)
        return self._page_items(tracks, page, size)

    async def get_artist_detail(
        self,
        artist_id: int,
        token: str | None = None,
    ) -> dict[str, Any]:
        headers: dict[str, str] | None = None
        if token:
            headers = {"Authorization": f"Bearer {token}"}
        response = await self._request(
            "GET",
            f"/api/v1/artists/{artist_id}",
            headers=headers,
        )
        return response.json()

    async def get_artist_catalog_releases(
        self,
        artist_id: int,
        token: str | None = None,
    ) -> dict[str, Any]:
        headers: dict[str, str] | None = None
        if token:
            headers = {"Authorization": f"Bearer {token}"}
        response = await self._request(
            "GET",
            f"/api/v1/artists/{artist_id}/catalog/releases",
            headers=headers,
        )
        return response.json()

    async def get_daily_playlist(
        self, telegram_id: int
    ) -> dict[str, Any]:
        token = await self._get_token_for_user(
            telegram_id
        )
        response = await self._request(
            "GET",
            "/api/v1/recommendations/daily-playlist",
            headers={
                "Authorization": f"Bearer {token}"
            },
        )
        return response.json()

    async def get_weekly_playlist(
        self, telegram_id: int
    ) -> dict[str, Any]:
        token = await self._get_token_for_user(
            telegram_id
        )
        response = await self._request(
            "GET",
            "/api/v1/recommendations/weekly-playlist",
            headers={
                "Authorization": f"Bearer {token}"
            },
        )
        return response.json()

    async def refresh_daily_playlist(
        self, telegram_id: int
    ) -> None:
        token = await self._get_token_for_user(
            telegram_id
        )
        await self._request(
            "POST",
            "/api/v1/recommendations/daily-playlist/refresh",
            headers={
                "Authorization": f"Bearer {token}"
            },
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
