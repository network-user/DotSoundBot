from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

_SESSION_TTL = 1800


@dataclass
class PlayerSession:
    chat_id: int
    user_id: int
    source: str
    internal_user_id: int = 0
    audio_message_ids: list[int] = field(
        default_factory=list
    )
    control_message_id: int = 0
    track_ids: list[int] = field(
        default_factory=list
    )
    page: int = 1
    has_more: bool = True
    last_active: float = field(
        default_factory=time.time
    )
    prefetched_tracks: list[dict[str, Any]] = field(
        default_factory=list
    )
    prefetched_urls: dict[int, str] = field(
        default_factory=dict
    )
    prefetched_total: int = 0
    prefetched_has_more: bool = False
    current_tracks: list[dict[str, Any]] = field(
        default_factory=list
    )
    history_batches: list[dict[str, Any]] = field(
        default_factory=list
    )
    total_tracks: int = 0
    shuffle_enabled: bool = False

    def touch(self) -> None:
        self.last_active = time.time()

    @property
    def expired(self) -> bool:
        return (
            time.time() - self.last_active
            > _SESSION_TTL
        )


class PlayerSessionManager:
    def __init__(self) -> None:
        self._sessions: dict[int, PlayerSession] = {}

    def get(
        self, user_id: int
    ) -> PlayerSession | None:
        session = self._sessions.get(user_id)
        if session and session.expired:
            self._sessions.pop(user_id, None)
            return None
        return session

    def create(
        self,
        chat_id: int,
        user_id: int,
        source: str,
    ) -> PlayerSession:
        session = PlayerSession(
            chat_id=chat_id,
            user_id=user_id,
            source=source,
        )
        self._sessions[user_id] = session
        return session

    def remove(self, user_id: int) -> None:
        self._sessions.pop(user_id, None)


player_sessions = PlayerSessionManager()
