from ipaddress import ip_address
from typing import Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})
_COMPOSE_BIND_HOSTS = frozenset({"0.0.0.0", "::"})


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    bot_token: str
    backend_base_url: str
    mini_app_url: str
    log_level: str = "INFO"
    # Caps aiogram, httpx, httpcore, aiohttp. DEBUG shows HTTP traces.
    log_third_party_level: str = "WARNING"
    debug: bool = False
    redact_logs: bool = True
    redact_log_identifiers: bool = True
    redis_url: str = "redis://localhost:6379/0"
    internal_api_port: int = 8081
    internal_api_host: str = "127.0.0.1"
    internal_api_compose_bind: bool = False
    internal_api_secret: str = ""
    throttle_rate_limit: float = 0.7
    throttle_callback_rate_limit: float = 0.35
    admin_alert_chat_id_allowlist: str = ""
    backup_notify_telegram_id: int = 0

    @model_validator(mode="after")
    def _validate_internal_api_bind(self) -> Self:
        host = self.internal_api_host.strip()
        if self.internal_api_compose_bind:
            if host in _COMPOSE_BIND_HOSTS:
                return self
            raise ValueError(
                "INTERNAL_API_COMPOSE_BIND=true requires "
                "INTERNAL_API_HOST=0.0.0.0 or ::; do not publish "
                "INTERNAL_API_PORT on the host."
            )
        if host.lower() in _LOOPBACK_HOSTS:
            return self
        try:
            if ip_address(host).is_loopback:
                return self
        except ValueError:
            pass
        raise ValueError(
            "INTERNAL_API_HOST must be loopback "
            "(127.0.0.1, ::1, or localhost); the bot's internal "
            "API must never be reachable from outside the host. "
            "For Docker Compose set INTERNAL_API_COMPOSE_BIND=true "
            "and INTERNAL_API_HOST=0.0.0.0 (see docker-compose.yml)."
        )


settings = BotSettings()
