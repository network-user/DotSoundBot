import io
import json
from unittest.mock import (
    AsyncMock,
    MagicMock,
    patch,
)

import pytest
from aiohttp.test_utils import make_mocked_request

from bot.api.internal import (
    _check_secret,
    create_internal_app,
    handle_download_audio,
    handle_profile_audios,
    handle_send_auth_code,
    handle_send_login_notification,
)

pytestmark = pytest.mark.anyio


def _make_request(
    method: str,
    path: str,
    headers: dict | None = None,
    match_info: dict | None = None,
    body: bytes | None = None,
    bot: AsyncMock | None = None,
    json_error: bool = False,
):
    app = MagicMock()
    app.__getitem__ = MagicMock(
        side_effect=(
            lambda k: bot if k == "bot" else None
        )
    )
    req = make_mocked_request(
        method,
        path,
        headers=headers or {},
        match_info=match_info or {},
        app=app,
    )
    if body is not None and not json_error:
        req._payload = MagicMock()
        req.json = AsyncMock(
            return_value=json.loads(body)
        )
        req.read = AsyncMock(return_value=body)
    elif json_error:
        req.json = AsyncMock(
            side_effect=Exception("bad json")
        )
    return req


# ------------------------------------------------------------------
# _check_secret
# ------------------------------------------------------------------


@patch("bot.api.internal.settings")
def test_check_secret_empty(
    mock_settings: MagicMock,
) -> None:
    mock_settings.internal_api_secret = ""
    req = _make_request("GET", "/test")

    assert _check_secret(req) is False


@patch("bot.api.internal.settings")
def test_check_secret_mismatch(
    mock_settings: MagicMock,
) -> None:
    mock_settings.internal_api_secret = "correct"
    req = _make_request(
        "GET",
        "/test",
        headers={"X-Internal-Secret": "wrong"},
    )

    assert _check_secret(req) is False


@patch("bot.api.internal.settings")
def test_check_secret_match(
    mock_settings: MagicMock,
) -> None:
    mock_settings.internal_api_secret = "correct"
    req = _make_request(
        "GET",
        "/test",
        headers={"X-Internal-Secret": "correct"},
    )

    assert _check_secret(req) is True


# ------------------------------------------------------------------
# handle_profile_audios
# ------------------------------------------------------------------


@patch("bot.api.internal.settings")
async def test_profile_audios_forbidden(
    mock_settings: MagicMock,
) -> None:
    mock_settings.internal_api_secret = "s"
    req = _make_request(
        "GET",
        "/internal/profile/1/audios",
        headers={"X-Internal-Secret": "bad"},
        match_info={"user_id": "1"},
    )

    resp = await handle_profile_audios(req)

    assert resp.status == 403


@patch("bot.api.internal.settings")
async def test_profile_audios_success(
    mock_settings: MagicMock,
) -> None:
    mock_settings.internal_api_secret = "s"
    bot = AsyncMock()

    audio1 = MagicMock()
    audio1.file_id = "fid1"
    audio1.file_unique_id = "uid1"
    audio1.title = "Song 1"
    audio1.performer = "Artist"
    audio1.duration = 200
    audio1.file_size = 5000
    audio1.mime_type = "audio/mpeg"

    result_mock = MagicMock()
    result_mock.audios = [audio1]
    result_mock.total_count = 1

    bot.get_user_profile_audios = AsyncMock(
        return_value=result_mock
    )

    req = _make_request(
        "GET",
        "/internal/profile/1/audios",
        headers={"X-Internal-Secret": "s"},
        match_info={"user_id": "1"},
        bot=bot,
    )

    resp = await handle_profile_audios(req)

    assert resp.status == 200
    data = json.loads(resp.body)
    assert data["total_count"] == 1
    assert len(data["audios"]) == 1
    assert data["audios"][0]["title"] == "Song 1"


@patch("bot.api.internal.settings")
async def test_profile_audios_exception(
    mock_settings: MagicMock,
) -> None:
    mock_settings.internal_api_secret = "s"
    bot = AsyncMock()
    bot.get_user_profile_audios = AsyncMock(
        side_effect=Exception("api error")
    )

    req = _make_request(
        "GET",
        "/internal/profile/1/audios",
        headers={"X-Internal-Secret": "s"},
        match_info={"user_id": "1"},
        bot=bot,
    )

    resp = await handle_profile_audios(req)

    assert resp.status == 500


# ------------------------------------------------------------------
# handle_download_audio
# ------------------------------------------------------------------


@patch("bot.api.internal.settings")
async def test_download_audio_forbidden(
    mock_settings: MagicMock,
) -> None:
    mock_settings.internal_api_secret = "s"
    req = _make_request(
        "POST",
        "/internal/download",
        headers={"X-Internal-Secret": "bad"},
        body=b'{"file_id": "abc"}',
    )

    resp = await handle_download_audio(req)

    assert resp.status == 403


@patch("bot.api.internal.settings")
async def test_download_audio_invalid_json(
    mock_settings: MagicMock,
) -> None:
    mock_settings.internal_api_secret = "s"
    bot = AsyncMock()
    req = _make_request(
        "POST",
        "/internal/download",
        headers={"X-Internal-Secret": "s"},
        bot=bot,
        json_error=True,
    )

    resp = await handle_download_audio(req)

    assert resp.status == 400


@patch("bot.api.internal.settings")
async def test_download_audio_missing_file_id(
    mock_settings: MagicMock,
) -> None:
    mock_settings.internal_api_secret = "s"
    bot = AsyncMock()
    req = _make_request(
        "POST",
        "/internal/download",
        headers={"X-Internal-Secret": "s"},
        body=b'{"file_id": ""}',
        bot=bot,
    )

    resp = await handle_download_audio(req)

    assert resp.status == 400
    data = json.loads(resp.body)
    assert data["error"] == "file_id required"


@patch("bot.api.internal.settings")
async def test_download_audio_success(
    mock_settings: MagicMock,
) -> None:
    mock_settings.internal_api_secret = "s"
    bot = AsyncMock()
    file_mock = MagicMock()
    file_mock.file_path = "music/test.mp3"
    file_mock.file_size = 1024
    bot.get_file = AsyncMock(return_value=file_mock)
    buf = io.BytesIO(b"audio-data")
    bot.download_file = AsyncMock(
        side_effect=lambda p, b: b.write(
            buf.getvalue()
        )
    )

    req = _make_request(
        "POST",
        "/internal/download",
        headers={"X-Internal-Secret": "s"},
        body=b'{"file_id": "abc123"}',
        bot=bot,
    )

    resp = await handle_download_audio(req)

    assert resp.status == 200
    assert resp.content_type == "audio/mpeg"


@patch("bot.api.internal.settings")
async def test_download_audio_no_file_path(
    mock_settings: MagicMock,
) -> None:
    mock_settings.internal_api_secret = "s"
    bot = AsyncMock()
    file_mock = MagicMock()
    file_mock.file_path = None
    file_mock.file_size = None
    bot.get_file = AsyncMock(return_value=file_mock)

    req = _make_request(
        "POST",
        "/internal/download",
        headers={"X-Internal-Secret": "s"},
        body=b'{"file_id": "abc123"}',
        bot=bot,
    )

    resp = await handle_download_audio(req)

    assert resp.status == 404


@patch("bot.api.internal.settings")
async def test_download_audio_too_large(
    mock_settings: MagicMock,
) -> None:
    mock_settings.internal_api_secret = "s"
    bot = AsyncMock()
    file_mock = MagicMock()
    file_mock.file_path = "music/big.mp3"
    file_mock.file_size = 30 * 1024 * 1024
    bot.get_file = AsyncMock(return_value=file_mock)

    req = _make_request(
        "POST",
        "/internal/download",
        headers={"X-Internal-Secret": "s"},
        body=b'{"file_id": "abc123"}',
        bot=bot,
    )

    resp = await handle_download_audio(req)

    assert resp.status == 413


@patch("bot.api.internal.settings")
async def test_download_audio_exception(
    mock_settings: MagicMock,
) -> None:
    mock_settings.internal_api_secret = "s"
    bot = AsyncMock()
    bot.get_file = AsyncMock(
        side_effect=Exception("fail")
    )

    req = _make_request(
        "POST",
        "/internal/download",
        headers={"X-Internal-Secret": "s"},
        body=b'{"file_id": "abc123"}',
        bot=bot,
    )

    resp = await handle_download_audio(req)

    assert resp.status == 500


# ------------------------------------------------------------------
# handle_send_auth_code
# ------------------------------------------------------------------


@patch("bot.api.internal.settings")
async def test_send_auth_code_forbidden(
    mock_settings: MagicMock,
) -> None:
    mock_settings.internal_api_secret = "s"
    req = _make_request(
        "POST",
        "/internal/auth-code",
        headers={"X-Internal-Secret": "bad"},
        body=b'{"telegram_id": 123, "code": "1234"}',
    )

    resp = await handle_send_auth_code(req)

    assert resp.status == 403


@patch("bot.api.internal.settings")
async def test_send_auth_code_invalid_json(
    mock_settings: MagicMock,
) -> None:
    mock_settings.internal_api_secret = "s"
    bot = AsyncMock()
    req = _make_request(
        "POST",
        "/internal/auth-code",
        headers={"X-Internal-Secret": "s"},
        bot=bot,
        json_error=True,
    )

    resp = await handle_send_auth_code(req)

    assert resp.status == 400


@patch("bot.api.internal.settings")
async def test_send_auth_code_missing_params(
    mock_settings: MagicMock,
) -> None:
    mock_settings.internal_api_secret = "s"
    bot = AsyncMock()
    req = _make_request(
        "POST",
        "/internal/auth-code",
        headers={"X-Internal-Secret": "s"},
        body=b'{"telegram_id": 0, "code": ""}',
        bot=bot,
    )

    resp = await handle_send_auth_code(req)

    assert resp.status == 400


@patch("bot.api.internal.settings")
async def test_send_auth_code_success(
    mock_settings: MagicMock,
) -> None:
    mock_settings.internal_api_secret = "s"
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    req = _make_request(
        "POST",
        "/internal/auth-code",
        headers={"X-Internal-Secret": "s"},
        body=b'{"telegram_id": 123, "code": "9999"}',
        bot=bot,
    )

    resp = await handle_send_auth_code(req)

    assert resp.status == 200
    data = json.loads(resp.body)
    assert data["sent"] is True
    bot.send_message.assert_awaited_once()


@patch("bot.api.internal.settings")
async def test_send_auth_code_send_fails(
    mock_settings: MagicMock,
) -> None:
    mock_settings.internal_api_secret = "s"
    bot = AsyncMock()
    bot.send_message = AsyncMock(
        side_effect=Exception("blocked")
    )
    req = _make_request(
        "POST",
        "/internal/auth-code",
        headers={"X-Internal-Secret": "s"},
        body=b'{"telegram_id": 123, "code": "9999"}',
        bot=bot,
    )

    resp = await handle_send_auth_code(req)

    assert resp.status == 500


# ------------------------------------------------------------------
# handle_send_login_notification
# ------------------------------------------------------------------


@patch("bot.api.internal.settings")
async def test_login_notification_forbidden(
    mock_settings: MagicMock,
) -> None:
    mock_settings.internal_api_secret = "s"
    req = _make_request(
        "POST",
        "/internal/login-notification",
        headers={"X-Internal-Secret": "bad"},
        body=b'{"telegram_id": 1}',
    )

    resp = await handle_send_login_notification(req)

    assert resp.status == 403


@patch("bot.api.internal.settings")
async def test_login_notification_invalid_json(
    mock_settings: MagicMock,
) -> None:
    mock_settings.internal_api_secret = "s"
    bot = AsyncMock()
    req = _make_request(
        "POST",
        "/internal/login-notification",
        headers={"X-Internal-Secret": "s"},
        bot=bot,
        json_error=True,
    )

    resp = await handle_send_login_notification(req)

    assert resp.status == 400


@patch("bot.api.internal.settings")
async def test_login_notification_missing_tg_id(
    mock_settings: MagicMock,
) -> None:
    mock_settings.internal_api_secret = "s"
    bot = AsyncMock()
    req = _make_request(
        "POST",
        "/internal/login-notification",
        headers={"X-Internal-Secret": "s"},
        body=b'{"telegram_id": 0}',
        bot=bot,
    )

    resp = await handle_send_login_notification(req)

    assert resp.status == 400


@patch("bot.api.internal.settings")
async def test_login_notification_success(
    mock_settings: MagicMock,
) -> None:
    mock_settings.internal_api_secret = "s"
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    body = json.dumps(
        {
            "telegram_id": 456,
            "ip": "1.2.3.4",
            "device": "Chrome",
            "time": "2025-01-01 12:00",
        }
    ).encode()
    req = _make_request(
        "POST",
        "/internal/login-notification",
        headers={"X-Internal-Secret": "s"},
        body=body,
        bot=bot,
    )

    resp = await handle_send_login_notification(req)

    assert resp.status == 200
    data = json.loads(resp.body)
    assert data["sent"] is True
    bot.send_message.assert_awaited_once()


@patch("bot.api.internal.settings")
async def test_login_notification_send_fails(
    mock_settings: MagicMock,
) -> None:
    mock_settings.internal_api_secret = "s"
    bot = AsyncMock()
    bot.send_message = AsyncMock(
        side_effect=Exception("blocked")
    )
    body = json.dumps(
        {
            "telegram_id": 456,
            "ip": "1.2.3.4",
            "device": "Chrome",
            "time": "2025-01-01 12:00",
        }
    ).encode()
    req = _make_request(
        "POST",
        "/internal/login-notification",
        headers={"X-Internal-Secret": "s"},
        body=body,
        bot=bot,
    )

    resp = await handle_send_login_notification(req)

    assert resp.status == 500


# ------------------------------------------------------------------
# create_internal_app
# ------------------------------------------------------------------


def test_create_internal_app() -> None:
    bot = AsyncMock()
    app = create_internal_app(bot)

    assert app["bot"] is bot
    routes = [
        r.resource.canonical
        for r in app.router.routes()
        if hasattr(r, "resource")
        and r.resource is not None
    ]
    assert len(routes) >= 4
