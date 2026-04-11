import pytest

from bot.utils.formatting import truncate


def test_truncate_short_string() -> None:
    assert truncate("hello", 10) == "hello"


def test_truncate_long_string() -> None:
    result = truncate("a" * 100, 10)
    assert len(result) <= 10
    assert result.endswith("...")


def test_truncate_exact_length() -> None:
    assert truncate("hello", 5) == "hello"
