from ipaddress import ip_address

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})


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
    internal_api_secret: str = ""
    throttle_rate_limit: float = 0.7
    throttle_callback_rate_limit: float = 0.35
    admin_alert_chat_id_allowlist: str = ""
    backup_notify_telegram_id: int = 0

    @field_validator("internal_api_host")
    @classmethod
    def _validate_internal_host(cls, v: str) -> str:
        host = v.strip()
        if host.lower() in _LOOPBACK_HOSTS:
            return host
        try:
            if ip_address(host).is_loopback:
                return host
        except ValueError:
            pass
        raise ValueError(
            "INTERNAL_API_HOST must be loopback "
            "(127.0.0.1, ::1, or localhost); the bot's internal "
            "API must never be reachable from outside the host."
        )


settings = BotSettings()
