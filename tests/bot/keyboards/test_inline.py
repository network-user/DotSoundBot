from unittest.mock import patch

import pytest

from bot.keyboards.inline import (
    about_kb,
    back_to_about_kb,
    back_to_menu_kb,
    help_keyboard,
    main_menu_kb,
    open_player_keyboard,
    player_control_kb,
    player_source_kb,
    playlists_keyboard,
    profile_kb,
    track_action_keyboard,
)


@patch("bot.keyboards.inline.settings")
def test_main_menu_kb_structure(
    mock_settings,
) -> None:
    mock_settings.mini_app_url = "https://app"
    kb = main_menu_kb("ru")

    buttons = [
        btn
        for row in kb.inline_keyboard
        for btn in row
    ]
    texts = [b.text for b in buttons]
    assert any("Профиль" in t for t in texts)
    assert any("О проекте" in t for t in texts)
    callbacks = [b.callback_data for b in buttons if b.callback_data]
    assert "menu:player" not in callbacks


def test_about_kb_has_sections() -> None:
    kb = about_kb("ru")

    buttons = [
        btn
        for row in kb.inline_keyboard
        for btn in row
    ]
    data = [b.callback_data for b in buttons]
    assert "about:features" in data
    assert "about:tech" in data
    assert "menu:main" in data


@pytest.mark.parametrize(
    ("kb_fn", "expected_data"),
    [
        (back_to_about_kb, "menu:about"),
        (back_to_menu_kb, "menu:main"),
    ],
)
def test_single_back_button(
    kb_fn, expected_data: str
) -> None:
    kb = kb_fn("ru")
    assert len(kb.inline_keyboard) == 1
    assert (
        kb.inline_keyboard[0][0].callback_data
        == expected_data
    )


@patch("bot.keyboards.inline.settings")
def test_profile_kb_has_back(
    mock_settings,
) -> None:
    mock_settings.mini_app_url = "https://app"
    kb = profile_kb("ru")

    buttons = [
        btn
        for row in kb.inline_keyboard
        for btn in row
    ]
    data = [b.callback_data for b in buttons]
    assert "menu:main" in data


def test_open_player_keyboard() -> None:
    kb = open_player_keyboard("https://app.test", "ru")

    assert len(kb.inline_keyboard) == 1
    btn = kb.inline_keyboard[0][0]
    assert btn.web_app is not None
    assert btn.web_app.url == "https://app.test"


@patch("bot.keyboards.inline.settings")
def test_track_action_keyboard(
    mock_settings,
) -> None:
    mock_settings.mini_app_url = "https://app"
    kb = track_action_keyboard(
        42, "https://app/mini_app/?track_id=42", "ru"
    )

    buttons = [
        btn
        for row in kb.inline_keyboard
        for btn in row
    ]
    data = [
        b.callback_data
        for b in buttons
        if b.callback_data
    ]
    assert "like_42" in data
    assert "dislike_42" in data


def test_playlists_keyboard_with_items() -> None:
    pls = [
        {"id": 1, "name": "Chill"},
        {"id": 2, "name": "Rock"},
    ]
    kb = playlists_keyboard(pls, "ru")

    buttons = [
        btn
        for row in kb.inline_keyboard
        for btn in row
    ]
    data = [b.callback_data for b in buttons]
    assert "playlist_1" in data
    assert "playlist_2" in data
    assert "create_playlist" in data


def test_player_source_kb() -> None:
    kb = player_source_kb("ru")

    buttons = [
        btn
        for row in kb.inline_keyboard
        for btn in row
    ]
    data = [b.callback_data for b in buttons]
    assert "player:src:my" in data
    assert "player:src:liked" in data
    assert "player:src:feed" in data


@pytest.mark.parametrize(
    (
        "track_count",
        "has_more",
        "can_go_back",
        "expect_next",
        "expect_prev",
    ),
    [
        (3, True, True, True, True),
        (2, False, False, False, False),
    ],
)
def test_player_control_kb(
    track_count: int,
    has_more: bool,
    can_go_back: bool,
    expect_next: bool,
    expect_prev: bool,
) -> None:
    kb = player_control_kb(
        track_count=track_count,
        has_more=has_more,
        lang="ru",
        can_go_back=can_go_back,
    )

    buttons = [
        btn
        for row in kb.inline_keyboard
        for btn in row
    ]
    data = [b.callback_data for b in buttons]
    for i in range(track_count):
        assert f"player:like:{i}" in data
    assert (
        "player:next" in data
    ) == expect_next
    assert (
        "player:prev" in data
    ) == expect_prev
    assert "player:shuffle" in data
    assert "player:menu" in data


def test_player_control_kb_shuffle_enabled_label() -> None:
    kb = player_control_kb(
        track_count=1,
        has_more=True,
        lang="en",
        shuffle_enabled=True,
    )
    buttons = [
        btn
        for row in kb.inline_keyboard
        for btn in row
    ]
    shuffle_buttons = [
        b for b in buttons if b.callback_data == "player:shuffle"
    ]
    assert len(shuffle_buttons) == 1
    assert "on" in (shuffle_buttons[0].text or "").lower()


@patch("bot.keyboards.inline.settings")
def test_help_keyboard(mock_settings) -> None:
    mock_settings.mini_app_url = "https://app"
    kb = help_keyboard("ru")

    buttons = [
        btn
        for row in kb.inline_keyboard
        for btn in row
    ]
    assert any(
        b.callback_data == "my_stats"
        for b in buttons
    )
