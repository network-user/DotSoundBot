from bot.config import BotSettings
from bot.utils.formatting import truncate


def test_bot_settings_importable() -> None:
    assert BotSettings


def test_truncate_short_text() -> None:
    assert truncate("hello", 10) == "hello"


def test_truncate_long_text() -> None:
    result = truncate("hello world", 7)
    assert len(result) == 7
    assert result.endswith("…")
