from bot.utils.formatting import (
    format_player_message,
    truncate,
)


def test_truncate_short_string_unchanged() -> None:
    assert truncate("hello", 10) == "hello"


def test_truncate_long_string_with_ellipsis() -> None:
    result = truncate("a" * 100, 10)

    assert len(result) == 10
    assert result.endswith("\u2026")
    assert result == "a" * 9 + "\u2026"


def test_truncate_exact_length_unchanged() -> None:
    assert truncate("hello", 5) == "hello"


def test_truncate_one_over() -> None:
    result = truncate("abcdef", 5)

    assert result == "abcd\u2026"
    assert len(result) == 5


def test_format_player_message_with_tracks() -> None:
    tracks = [
        {"title": "Song A", "artist": "Art1"},
        {"title": "Song B", "performer": "Art2"},
    ]

    result = format_player_message(
        "my", tracks, page=1, total=10
    )

    assert "Мои треки" in result
    assert "Song A" in result
    assert "Art1" in result
    assert "Song B" in result
    assert "1\u20132 из 10" in result


def test_format_player_message_empty_tracks() -> None:
    result = format_player_message(
        "feed", [], page=1, total=0
    )

    assert "Нет треков." in result


def test_format_player_message_with_total() -> None:
    tracks = [
        {"title": "X"},
    ]

    result = format_player_message(
        "liked", tracks, page=2, total=5
    )

    assert "Лайки" in result
    assert "2\u20132 из 5" in result
