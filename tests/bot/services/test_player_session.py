import time
from unittest.mock import patch

from bot.services.player_session import (
    PlayerSession,
    PlayerSessionManager,
)


def test_create_returns_new_session() -> None:
    mgr = PlayerSessionManager()

    session = mgr.create(
        chat_id=100, user_id=1, source="my"
    )

    assert session.chat_id == 100
    assert session.user_id == 1
    assert session.source == "my"
    assert session.page == 1


def test_get_returns_existing_session() -> None:
    mgr = PlayerSessionManager()
    created = mgr.create(
        chat_id=100, user_id=1, source="feed"
    )

    fetched = mgr.get(1)

    assert fetched is created


def test_get_returns_none_for_expired() -> None:
    mgr = PlayerSessionManager()
    session = mgr.create(
        chat_id=100, user_id=1, source="my"
    )
    session.last_active = time.time() - 2000

    assert mgr.get(1) is None


def test_get_returns_none_for_missing() -> None:
    mgr = PlayerSessionManager()

    assert mgr.get(999) is None


def test_remove_deletes_session() -> None:
    mgr = PlayerSessionManager()
    mgr.create(
        chat_id=100, user_id=1, source="my"
    )

    mgr.remove(1)

    assert mgr.get(1) is None


def test_cleanup_removes_expired() -> None:
    mgr = PlayerSessionManager()
    s1 = mgr.create(
        chat_id=100, user_id=1, source="my"
    )
    mgr.create(
        chat_id=200, user_id=2, source="feed"
    )
    s1.last_active = time.time() - 2000

    removed = mgr.cleanup()

    assert removed == 1
    assert mgr.get(1) is None
    assert mgr.get(2) is not None


def test_touch_updates_last_active() -> None:
    session = PlayerSession(
        chat_id=1, user_id=1, source="my"
    )
    old = session.last_active
    with patch(
        "bot.services.player_session.time.time",
        return_value=old + 100,
    ):
        session.touch()

    assert session.last_active > old


def test_expired_property() -> None:
    session = PlayerSession(
        chat_id=1, user_id=1, source="my"
    )

    assert session.expired is False

    session.last_active = time.time() - 2000

    assert session.expired is True
