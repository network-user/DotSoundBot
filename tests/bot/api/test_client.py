from unittest.mock import AsyncMock, patch

import httpx
import pytest
from dirty_equals import HasLen, IsPartialDict

from bot.api.client import BackendClient, BackendError

pytestmark = pytest.mark.anyio


def _resp(
    status: int,
    json_data: dict | list | None = None,
    text: str = "",
) -> httpx.Response:
    request = httpx.Request("GET", "http://test")
    if json_data is not None:
        import json as _json

        return httpx.Response(
            status,
            content=_json.dumps(json_data).encode(),
            headers={
                "content-type": "application/json"
            },
            request=request,
        )
    return httpx.Response(
        status, text=text, request=request
    )


@pytest.fixture
def _patch_settings():
    with patch("bot.api.client.settings") as s:
        s.backend_base_url = "http://test:8000"
        s.internal_api_secret = "secret"
        yield s


@pytest.fixture
def client(_patch_settings):
    return BackendClient()


# ------------------------------------------------------------------
# upload_audio
# ------------------------------------------------------------------


async def test_upload_audio_success(
    client: BackendClient,
) -> None:
    resp = _resp(200, {"id": 42, "title": "Song"})
    client._client = AsyncMock()
    client._client.request = AsyncMock(
        return_value=resp
    )
    client._get_token_for_user = AsyncMock(
        return_value="tok"
    )

    result = await client.upload_audio(
        file_bytes=b"data",
        filename="song.mp3",
        content_type="audio/mpeg",
        title="Song",
        uploader_id=1,
    )

    assert result == IsPartialDict(
        id=42, title="Song"
    )


async def test_upload_audio_without_uploader(
    client: BackendClient,
) -> None:
    resp = _resp(200, {"id": 43, "title": "Song2"})
    client._client = AsyncMock()
    client._client.request = AsyncMock(
        return_value=resp
    )

    result = await client.upload_audio(
        file_bytes=b"data",
        filename="song.mp3",
        content_type="audio/mpeg",
        title="Song2",
    )

    assert result == IsPartialDict(id=43)


async def test_upload_audio_token_failure_continues(
    client: BackendClient,
) -> None:
    resp = _resp(200, {"id": 44, "title": "Song3"})
    client._client = AsyncMock()
    client._client.request = AsyncMock(
        return_value=resp
    )
    client._get_token_for_user = AsyncMock(
        side_effect=Exception("token fail")
    )

    result = await client.upload_audio(
        file_bytes=b"data",
        filename="song.mp3",
        content_type="audio/mpeg",
        title="Song3",
        uploader_id=1,
    )

    assert result == IsPartialDict(id=44)


async def test_upload_audio_backend_error(
    client: BackendClient,
) -> None:
    resp = _resp(500, text="fail")
    client._client = AsyncMock()
    client._client.request = AsyncMock(
        return_value=resp
    )
    client._get_token_for_user = AsyncMock(
        return_value="tok"
    )

    with pytest.raises(BackendError) as exc_info:
        await client.upload_audio(
            file_bytes=b"data",
            filename="s.mp3",
            content_type="audio/mpeg",
            title="S",
            uploader_id=1,
        )

    assert exc_info.value.status_code == 500


# ------------------------------------------------------------------
# toggle_like / toggle_dislike
# ------------------------------------------------------------------


async def test_toggle_like(
    client: BackendClient,
) -> None:
    resp = _resp(200, {"liked": True})
    client._client = AsyncMock()
    client._client.request = AsyncMock(
        return_value=resp
    )

    result = await client.toggle_like(1, 10)

    assert result == IsPartialDict(liked=True)


async def test_toggle_dislike(
    client: BackendClient,
) -> None:
    resp = _resp(200, {"disliked": True})
    client._client = AsyncMock()
    client._client.request = AsyncMock(
        return_value=resp
    )

    result = await client.toggle_dislike(1, 10)

    assert result == IsPartialDict(disliked=True)


# ------------------------------------------------------------------
# get_user_profile / get_user_stats
# ------------------------------------------------------------------


async def test_get_user_profile_success(
    client: BackendClient,
) -> None:
    resp = _resp(
        200, {"id": 5, "first_name": "Alice"}
    )
    client._client = AsyncMock()
    client._client.request = AsyncMock(
        return_value=resp
    )

    result = await client.get_user_profile(123)

    assert result == IsPartialDict(
        id=5, first_name="Alice"
    )


async def test_get_user_profile_backend_error(
    client: BackendClient,
) -> None:
    resp = _resp(404, text="not found")
    client._client = AsyncMock()
    client._client.request = AsyncMock(
        return_value=resp
    )

    with pytest.raises(BackendError) as exc_info:
        await client.get_user_profile(999)

    assert exc_info.value.status_code == 404


async def test_get_user_stats(
    client: BackendClient,
) -> None:
    resp = _resp(
        200, {"total_tracks": 5, "total_plays": 20}
    )
    client._client = AsyncMock()
    client._client.request = AsyncMock(
        return_value=resp
    )

    result = await client.get_user_stats(1)

    assert result == IsPartialDict(total_tracks=5)


# ------------------------------------------------------------------
# get_login_history
# ------------------------------------------------------------------


async def test_get_login_history_list(
    client: BackendClient,
) -> None:
    resp = _resp(200, [{"ip": "1.2.3.4"}])
    client._client = AsyncMock()
    client._client.request = AsyncMock(
        return_value=resp
    )

    result = await client.get_login_history(1)

    assert isinstance(result, list)
    assert result[0] == IsPartialDict(
        ip="1.2.3.4"
    )


async def test_get_login_history_non_list(
    client: BackendClient,
) -> None:
    resp = _resp(200, {"error": "unexpected"})
    client._client = AsyncMock()
    client._client.request = AsyncMock(
        return_value=resp
    )

    result = await client.get_login_history(1)

    assert result == []


# ------------------------------------------------------------------
# get_user_playlists
# ------------------------------------------------------------------


async def test_get_user_playlists_success(
    client: BackendClient,
) -> None:
    resp = _resp(200, [{"id": 1, "name": "Chill"}])
    client._client = AsyncMock()
    client._client.request = AsyncMock(
        return_value=resp
    )
    client._get_token_for_user = AsyncMock(
        return_value="tok"
    )

    result = await client.get_user_playlists(1)

    assert result == HasLen(1)
    assert result[0] == IsPartialDict(name="Chill")


async def test_get_user_playlists_non_list(
    client: BackendClient,
) -> None:
    resp = _resp(200, {"error": "unexpected"})
    client._client = AsyncMock()
    client._client.request = AsyncMock(
        return_value=resp
    )
    client._get_token_for_user = AsyncMock(
        return_value="tok"
    )

    result = await client.get_user_playlists(1)

    assert result == []


async def test_get_user_playlists_token_failure(
    client: BackendClient,
) -> None:
    resp = _resp(200, [{"id": 1}])
    client._client = AsyncMock()
    client._client.request = AsyncMock(
        return_value=resp
    )
    client._get_token_for_user = AsyncMock(
        side_effect=Exception("fail")
    )

    result = await client.get_user_playlists(1)

    assert result == HasLen(1)


# ------------------------------------------------------------------
# create_playlist
# ------------------------------------------------------------------


async def test_create_playlist_success(
    client: BackendClient,
) -> None:
    resp = _resp(
        201, {"id": 10, "name": "My Playlist"}
    )
    client._client = AsyncMock()
    client._client.request = AsyncMock(
        return_value=resp
    )
    client._get_token_for_user = AsyncMock(
        return_value="tok"
    )

    result = await client.create_playlist(
        owner_id=1, name="My Playlist"
    )

    assert result == IsPartialDict(
        id=10, name="My Playlist"
    )


async def test_create_playlist_token_failure(
    client: BackendClient,
) -> None:
    resp = _resp(201, {"id": 11, "name": "P"})
    client._client = AsyncMock()
    client._client.request = AsyncMock(
        return_value=resp
    )
    client._get_token_for_user = AsyncMock(
        side_effect=Exception("fail")
    )

    result = await client.create_playlist(
        owner_id=1, name="P"
    )

    assert result == IsPartialDict(id=11)


# ------------------------------------------------------------------
# get_internal_token
# ------------------------------------------------------------------


async def test_get_internal_token(
    client: BackendClient,
) -> None:
    resp = _resp(
        200,
        {"access_token": "tok", "user_id": 5},
    )
    client._client = AsyncMock()
    client._client.request = AsyncMock(
        return_value=resp
    )

    result = await client.get_internal_token(
        123, "sec"
    )

    assert result == IsPartialDict(
        access_token="tok", user_id=5
    )


# ------------------------------------------------------------------
# get_stream_url
# ------------------------------------------------------------------


async def test_get_stream_url(
    client: BackendClient,
) -> None:
    resp = _resp(
        200, {"url": "https://cdn/track.mp3"}
    )
    client._client = AsyncMock()
    client._client.request = AsyncMock(
        return_value=resp
    )

    result = await client.get_stream_url(1, "tok")

    assert result == "https://cdn/track.mp3"


# ------------------------------------------------------------------
# get_my_tracks
# ------------------------------------------------------------------


async def test_get_my_tracks(
    client: BackendClient,
) -> None:
    resp = _resp(
        200,
        {
            "items": [{"id": 1}],
            "total": 1,
        },
    )
    client._client = AsyncMock()
    client._client.request = AsyncMock(
        return_value=resp
    )

    result = await client.get_my_tracks(
        "tok", page=1, size=3, playable=True
    )

    assert result == IsPartialDict(total=1)


async def test_get_my_tracks_not_playable(
    client: BackendClient,
) -> None:
    resp = _resp(
        200,
        {"items": [{"id": 1}], "total": 1},
    )
    client._client = AsyncMock()
    client._client.request = AsyncMock(
        return_value=resp
    )

    result = await client.get_my_tracks("tok")

    assert result == IsPartialDict(total=1)


# ------------------------------------------------------------------
# get_liked_tracks
# ------------------------------------------------------------------


async def test_get_liked_tracks(
    client: BackendClient,
) -> None:
    resp = _resp(
        200, {"items": [{"id": 2}]}
    )
    client._client = AsyncMock()
    client._client.request = AsyncMock(
        return_value=resp
    )

    result = await client.get_liked_tracks(1, "tok")

    assert result == IsPartialDict(
        items=HasLen(1)
    )


# ------------------------------------------------------------------
# get_feed_tracks
# ------------------------------------------------------------------


async def test_get_feed_tracks(
    client: BackendClient,
) -> None:
    resp = _resp(
        200,
        {"items": [{"id": 3}], "total": 1},
    )
    client._client = AsyncMock()
    client._client.request = AsyncMock(
        return_value=resp
    )

    result = await client.get_feed_tracks(
        page=1, size=3, playable=True
    )

    assert result == IsPartialDict(total=1)


async def test_get_feed_tracks_not_playable(
    client: BackendClient,
) -> None:
    resp = _resp(
        200,
        {"items": [{"id": 3}], "total": 1},
    )
    client._client = AsyncMock()
    client._client.request = AsyncMock(
        return_value=resp
    )

    result = await client.get_feed_tracks()

    assert result == IsPartialDict(total=1)


# ------------------------------------------------------------------
# _get_token_for_user
# ------------------------------------------------------------------


async def test_get_token_for_user_no_secret(
    client: BackendClient,
    _patch_settings,
) -> None:
    _patch_settings.internal_api_secret = ""

    with pytest.raises(BackendError) as exc_info:
        await client._get_token_for_user(123)

    assert exc_info.value.status_code == 500


async def test_get_token_for_user_success(
    client: BackendClient,
) -> None:
    resp = _resp(
        200,
        {"access_token": "tok123", "user_id": 5},
    )
    client._client = AsyncMock()
    client._client.request = AsyncMock(
        return_value=resp
    )

    result = await client._get_token_for_user(1)

    assert result == "tok123"


# ------------------------------------------------------------------
# error handling
# ------------------------------------------------------------------


async def test_timeout_handling(
    client: BackendClient,
) -> None:
    client._client = AsyncMock()
    client._client.request = AsyncMock(
        side_effect=httpx.ReadTimeout("timeout")
    )

    with pytest.raises(BackendError) as exc_info:
        await client.get_user_profile(1)

    assert exc_info.value.status_code == 504


async def test_network_error_handling(
    client: BackendClient,
) -> None:
    client._client = AsyncMock()
    client._client.request = AsyncMock(
        side_effect=httpx.ConnectError("refused")
    )

    with pytest.raises(BackendError) as exc_info:
        await client.get_user_profile(1)

    assert exc_info.value.status_code == 502


async def test_generic_http_error(
    client: BackendClient,
) -> None:
    client._client = AsyncMock()
    client._client.request = AsyncMock(
        side_effect=httpx.HTTPError("generic")
    )

    with pytest.raises(BackendError) as exc_info:
        await client.get_user_profile(1)

    assert exc_info.value.status_code == 500


# ------------------------------------------------------------------
# close / context manager
# ------------------------------------------------------------------


async def test_close(
    client: BackendClient,
) -> None:
    client._client = AsyncMock()
    client._client.aclose = AsyncMock()

    await client.close()

    client._client.aclose.assert_awaited_once()


async def test_context_manager(
    _patch_settings,
) -> None:
    async with BackendClient() as c:
        assert isinstance(c, BackendClient)


# ------------------------------------------------------------------
# BackendError
# ------------------------------------------------------------------


def test_backend_error_str() -> None:
    err = BackendError(404, "not found")

    assert "404" in str(err)
    assert "not found" in str(err)
    assert err.status_code == 404
    assert err.detail == "not found"
