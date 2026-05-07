import pytest

from bot.utils.formatting import (
    format_player_message,
    truncate,
)


@pytest.mark.parametrize(
    ("text", "max_len", "expected"),
    [
        ("hello", 10, "hello"),
        ("a" * 100, 10, "a" * 9 + "\u2026"),
        ("hello", 5, "hello"),
        ("abcdef", 5, "abcd\u2026"),
    ],
)
def test_truncate(
    text: str, max_len: int, expected: str
) -> None:
    result = truncate(text, max_len)
    assert result == expected
    assert len(result) <= max_len


def test_format_player_message_with_tracks() -> None:
    tracks = [
        {"title": "Song A", "artist": "Art1"},
        {"title": "Song B", "performer": "Art2"},
    ]

    result = format_player_message(
        "my", tracks, page=1, total=10, lang="ru"
    )

    assert "Мои треки" in result
    assert "Song A" in result
    assert "Art1" in result
    assert "Song B" in result
    assert "1\u20132 из 10" in result


def test_format_player_message_empty_tracks() -> None:
    result = format_player_message(
        "feed", [], page=1, total=0, lang="ru"
    )

    assert "Нет треков." in result


def test_format_player_message_with_total() -> None:
    tracks = [
        {"title": "X"},
    ]

    result = format_player_message(
        "liked", tracks, page=2, total=5, lang="ru"
    )

    assert "Лайки" in result
    assert "2\u20132 из 5" in result


def test_format_player_message_with_follows_label() -> None:
    tracks = [{"title": "Track X", "artist": "Artist Y"}]

    result = format_player_message(
        "follows", tracks, page=1, total=1, lang="ru"
    )

    assert "Подписки" in result
