from unittest.mock import (
    AsyncMock,
    MagicMock,
    patch,
)

import pytest


def _make_message(
    text: str = "/start web_login",
    user_id: int = 1,
):
    msg = AsyncMock()
    msg.from_user = MagicMock()
    msg.from_user.id = user_id
    msg.text = text
    msg.answer = AsyncMock()
    return msg


@pytest.mark.anyio
@patch("bot.handlers.web_auth.settings")
@patch("httpx.AsyncClient")
@patch(
    "bot.handlers.web_auth.auth_generate_code_url",
    return_value="http://test/api/v1/auth/code",
)
@patch(
    "bot.handlers.web_auth.build_internal_headers",
    return_value={"X-Internal-Secret": "s"},
)
async def test_web_login_success(
    _mock_headers: MagicMock,
    _mock_url: MagicMock,
    mock_httpx_cls: MagicMock,
    mock_settings: MagicMock,
) -> None:
    from bot.handlers.web_auth import (
        cmd_start_web_login,
    )

    mock_settings.backend_base_url = "http://test"
    mock_settings.internal_api_secret = "s"
    mock_settings.mini_app_url = "https://app.test"

    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"code": "123456"}
    client_ctx = AsyncMock()
    client_ctx.post = AsyncMock(return_value=resp)
    mock_httpx_cls.return_value.__aenter__ = (
        AsyncMock(return_value=client_ctx)
    )
    mock_httpx_cls.return_value.__aexit__ = (
        AsyncMock(return_value=False)
    )

    msg = _make_message()

    await cmd_start_web_login(msg)

    msg.answer.assert_awaited_once()
    text = msg.answer.call_args[0][0]
    assert "123456" in text


@pytest.mark.anyio
@patch("bot.handlers.web_auth.settings")
@patch("httpx.AsyncClient")
@patch(
    "bot.handlers.web_auth.auth_generate_code_url",
    return_value="http://test/api/v1/auth/code",
)
@patch(
    "bot.handlers.web_auth.build_internal_headers",
    return_value={"X-Internal-Secret": "s"},
)
async def test_web_login_backend_error(
    _mock_headers: MagicMock,
    _mock_url: MagicMock,
    mock_httpx_cls: MagicMock,
    mock_settings: MagicMock,
) -> None:
    from bot.handlers.web_auth import (
        cmd_start_web_login,
    )

    mock_settings.backend_base_url = "http://test"
    mock_settings.internal_api_secret = "s"

    resp = MagicMock()
    resp.status_code = 500
    client_ctx = AsyncMock()
    client_ctx.post = AsyncMock(return_value=resp)
    mock_httpx_cls.return_value.__aenter__ = (
        AsyncMock(return_value=client_ctx)
    )
    mock_httpx_cls.return_value.__aexit__ = (
        AsyncMock(return_value=False)
    )

    msg = _make_message()

    await cmd_start_web_login(msg)

    msg.answer.assert_awaited_once()
    text = msg.answer.call_args[0][0]
    assert "Не удалось" in text


@pytest.mark.anyio
async def test_web_login_no_user() -> None:
    from bot.handlers.web_auth import (
        cmd_start_web_login,
    )

    msg = AsyncMock()
    msg.from_user = None
    msg.answer = AsyncMock()

    await cmd_start_web_login(msg)

    msg.answer.assert_not_awaited()
