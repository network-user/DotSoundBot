from unittest.mock import (
    AsyncMock,
    MagicMock,
    patch,
)

import pytest
from aiogram.types import CallbackQuery

pytestmark = pytest.mark.anyio


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
        "INFO", redact=True, json_output=True
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
        "DEBUG", redact=False, json_output=False
    )


async def test_global_error_handler_callback_query() -> None:
    from bot.main import _global_error_handler

    callback = MagicMock(spec=CallbackQuery)
    callback.answer = AsyncMock()
    update = MagicMock()
    update.callback_query = callback
    update.inline_query = None
    update.message = None
    event = MagicMock()
    event.update = update
    event.exception = RuntimeError("x")

    await _global_error_handler(event)

    callback.answer.assert_awaited_once()
