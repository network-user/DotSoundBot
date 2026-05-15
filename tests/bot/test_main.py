from unittest.mock import (
    ANY,
    AsyncMock,
    MagicMock,
    patch,
)

import pytest
from aiogram.types import CallbackQuery

pytestmark = pytest.mark.anyio


def test_normalize_proxy_url_strips_env_artifacts() -> None:
    from bot.main import _normalize_proxy_url

    assert (
        _normalize_proxy_url('"socks5://127.0.0.1:9050 # tor"')
        == "socks5://127.0.0.1:9050"
    )


def test_split_proxy_urls_supports_comma_separated_list() -> None:
    from bot.main import _split_proxy_urls

    assert _split_proxy_urls(
        "socks5://u:p@10.0.0.1:9050,"
        " socks5://u:p@10.0.0.2:9050"
    ) == [
        "socks5://u:p@10.0.0.1:9050",
        "socks5://u:p@10.0.0.2:9050",
    ]


@patch("bot.main.AiohttpSession")
def test_create_telegram_session_invalid_proxy_falls_back(
    mock_session_cls: MagicMock,
) -> None:
    from bot.main import _create_telegram_session

    mock_session_cls.side_effect = ValueError("Invalid port component")

    assert _create_telegram_session("socks5://127.0.0.1:bad") is None
    mock_session_cls.assert_called_once_with(
        proxy="socks5://127.0.0.1:bad"
    )


@patch("bot.main.AiohttpSession")
def test_create_telegram_session_uses_first_valid_proxy_candidate(
    mock_session_cls: MagicMock,
) -> None:
    from bot.main import _create_telegram_session

    valid_session = MagicMock()
    mock_session_cls.side_effect = [
        ValueError("Invalid port component"),
        valid_session,
    ]

    session = _create_telegram_session(
        "socks5://127.0.0.1:bad,socks5://127.0.0.1:9050"
    )

    assert session is valid_session
    assert mock_session_cls.call_args_list[0].kwargs == {
        "proxy": "socks5://127.0.0.1:bad"
    }
    assert mock_session_cls.call_args_list[1].kwargs == {
        "proxy": "socks5://127.0.0.1:9050"
    }


@patch("bot.main.web")
@patch("bot.main.create_internal_app")
@patch("bot.main.Dispatcher")
@patch("bot.main.Bot")
@patch("bot.main.configure_logging")
@patch("bot.main.settings")
async def test_main_startup_and_shutdown(
    mock_settings: MagicMock,
    mock_configure: MagicMock,
    mock_bot_cls: MagicMock,
    mock_dp_cls: MagicMock,
    mock_create_app: MagicMock,
    mock_web: MagicMock,
) -> None:
    from bot.main import main

    mock_settings.bot_token = "test:token"
    mock_settings.log_level = "INFO"
    mock_settings.redact_logs = True
    mock_settings.debug = False
    mock_settings.mini_app_url = "https://test.app"
    mock_settings.internal_api_port = 8081
    mock_settings.telegram_api_proxy_url = ""

    bot = AsyncMock()
    bot.set_chat_menu_button = AsyncMock()
    bot.session = AsyncMock()
    bot.session.close = AsyncMock()
    mock_bot_cls.return_value = bot

    dp = MagicMock()
    dp.update = MagicMock()
    dp.update.outer_middleware = MagicMock()
    dp.message = MagicMock()
    dp.message.middleware = MagicMock()
    dp.include_router = MagicMock()
    dp.resolve_used_update_types = MagicMock(
        return_value=["message", "callback_query"]
    )
    dp.start_polling = AsyncMock()
    mock_dp_cls.return_value = dp

    internal_app = MagicMock()
    mock_create_app.return_value = internal_app

    runner = AsyncMock()
    runner.setup = AsyncMock()
    runner.cleanup = AsyncMock()
    mock_web.AppRunner.return_value = runner

    site = AsyncMock()
    site.start = AsyncMock()
    mock_web.TCPSite.return_value = site

    await main()

    mock_configure.assert_called_once_with(
        "INFO",
        redact=True,
        redact_identifiers=ANY,
        json_output=True,
        third_party_level=ANY,
    )
    bot.set_chat_menu_button.assert_awaited_once()
    runner.setup.assert_awaited_once()
    site.start.assert_awaited_once()
    dp.start_polling.assert_awaited_once()
    runner.cleanup.assert_awaited_once()
    bot.session.close.assert_awaited_once()


@patch("bot.main.web")
@patch("bot.main.create_internal_app")
@patch("bot.main.Dispatcher")
@patch("bot.main.AiohttpSession")
@patch("bot.main.Bot")
@patch("bot.main.configure_logging")
@patch("bot.main.settings")
async def test_main_configures_telegram_api_proxy(
    mock_settings: MagicMock,
    mock_configure: MagicMock,
    mock_bot_cls: MagicMock,
    mock_session_cls: MagicMock,
    mock_dp_cls: MagicMock,
    mock_create_app: MagicMock,
    mock_web: MagicMock,
) -> None:
    from bot.main import main

    mock_settings.bot_token = "test:token"
    mock_settings.log_level = "INFO"
    mock_settings.redact_logs = True
    mock_settings.redact_log_identifiers = True
    mock_settings.log_third_party_level = "WARNING"
    mock_settings.debug = False
    mock_settings.mini_app_url = "https://test.app"
    mock_settings.internal_api_host = "127.0.0.1"
    mock_settings.internal_api_port = 8081
    mock_settings.telegram_api_proxy_url = "socks5://127.0.0.1:9050"

    proxy_session = MagicMock()
    mock_session_cls.return_value = proxy_session

    bot = AsyncMock()
    bot.set_chat_menu_button = AsyncMock()
    bot.session = AsyncMock()
    bot.session.close = AsyncMock()
    mock_bot_cls.return_value = bot

    dp = MagicMock()
    dp.update = MagicMock()
    dp.update.outer_middleware = MagicMock()
    dp.message = MagicMock()
    dp.message.middleware = MagicMock()
    dp.callback_query = MagicMock()
    dp.callback_query.middleware = MagicMock()
    dp.inline_query = MagicMock()
    dp.inline_query.middleware = MagicMock()
    dp.errors = MagicMock()
    dp.errors.register = MagicMock()
    dp.include_router = MagicMock()
    dp.resolve_used_update_types = MagicMock(return_value=[])
    dp.start_polling = AsyncMock()
    mock_dp_cls.return_value = dp

    runner = AsyncMock()
    runner.setup = AsyncMock()
    runner.cleanup = AsyncMock()
    mock_web.AppRunner.return_value = runner
    site = AsyncMock()
    site.start = AsyncMock()
    mock_web.TCPSite.return_value = site
    mock_create_app.return_value = MagicMock()

    await main()

    mock_session_cls.assert_called_once_with(
        proxy="socks5://127.0.0.1:9050"
    )
    assert mock_bot_cls.call_args.kwargs["session"] is proxy_session


@patch("bot.main.web")
@patch("bot.main.create_internal_app")
@patch("bot.main.Dispatcher")
@patch("bot.main.Bot")
@patch("bot.main.configure_logging")
@patch("bot.main.settings")
async def test_main_polling_exception_cleanup(
    mock_settings: MagicMock,
    mock_configure: MagicMock,
    mock_bot_cls: MagicMock,
    mock_dp_cls: MagicMock,
    mock_create_app: MagicMock,
    mock_web: MagicMock,
) -> None:
    from bot.main import main

    mock_settings.bot_token = "test:token"
    mock_settings.log_level = "DEBUG"
    mock_settings.redact_logs = False
    mock_settings.debug = True
    mock_settings.mini_app_url = "https://test.app"
    mock_settings.internal_api_port = 8081
    mock_settings.telegram_api_proxy_url = ""

    bot = AsyncMock()
    bot.set_chat_menu_button = AsyncMock()
    bot.session = AsyncMock()
    bot.session.close = AsyncMock()
    mock_bot_cls.return_value = bot

    dp = MagicMock()
    dp.update = MagicMock()
    dp.update.outer_middleware = MagicMock()
    dp.message = MagicMock()
    dp.message.middleware = MagicMock()
    dp.include_router = MagicMock()
    dp.resolve_used_update_types = MagicMock(
        return_value=[]
    )
    dp.start_polling = AsyncMock(
        side_effect=KeyboardInterrupt
    )
    mock_dp_cls.return_value = dp

    runner = AsyncMock()
    runner.setup = AsyncMock()
    runner.cleanup = AsyncMock()
    mock_web.AppRunner.return_value = runner

    site = AsyncMock()
    site.start = AsyncMock()
    mock_web.TCPSite.return_value = site

    mock_create_app.return_value = MagicMock()

    with pytest.raises(KeyboardInterrupt):
        await main()

    runner.cleanup.assert_awaited_once()
    bot.session.close.assert_awaited_once()


@patch("bot.main.web")
@patch("bot.main.create_internal_app")
@patch("bot.main.Dispatcher")
@patch("bot.main.Bot")
@patch("bot.main.configure_logging")
@patch("bot.main.settings")
async def test_main_debug_mode_no_json(
    mock_settings: MagicMock,
    mock_configure: MagicMock,
    mock_bot_cls: MagicMock,
    mock_dp_cls: MagicMock,
    mock_create_app: MagicMock,
    mock_web: MagicMock,
) -> None:
    from bot.main import main

    mock_settings.bot_token = "test:token"
    mock_settings.log_level = "DEBUG"
    mock_settings.redact_logs = False
    mock_settings.debug = True
    mock_settings.mini_app_url = "https://test.app"
    mock_settings.internal_api_port = 8081
    mock_settings.telegram_api_proxy_url = ""

    bot = AsyncMock()
    bot.set_chat_menu_button = AsyncMock()
    bot.session = AsyncMock()
    bot.session.close = AsyncMock()
    mock_bot_cls.return_value = bot

    dp = MagicMock()
    dp.update = MagicMock()
    dp.update.outer_middleware = MagicMock()
    dp.message = MagicMock()
    dp.message.middleware = MagicMock()
    dp.include_router = MagicMock()
    dp.resolve_used_update_types = MagicMock(
        return_value=[]
    )
    dp.start_polling = AsyncMock()
    mock_dp_cls.return_value = dp

    runner = AsyncMock()
    runner.setup = AsyncMock()
    runner.cleanup = AsyncMock()
    mock_web.AppRunner.return_value = runner

    site = AsyncMock()
    site.start = AsyncMock()
    mock_web.TCPSite.return_value = site

    mock_create_app.return_value = MagicMock()

    await main()

    mock_configure.assert_called_once_with(
        "DEBUG",
        redact=False,
        redact_identifiers=ANY,
        json_output=False,
        third_party_level=ANY,
    )


async def test_global_error_handler_callback_query() -> None:
    from bot.main import _global_error_handler

    callback = MagicMock(spec=CallbackQuery)
    callback.answer = AsyncMock()
    callback.from_user = MagicMock()
    callback.from_user.language_code = "ru"
    update = MagicMock()
    update.callback_query = callback
    update.inline_query = None
    update.message = None
    event = MagicMock()
    event.update = update
    event.exception = RuntimeError("x")

    await _global_error_handler(event)

    callback.answer.assert_awaited_once()
