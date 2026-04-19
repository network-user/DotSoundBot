from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    bot_token: str
    backend_base_url: str
    mini_app_url: str
    log_level: str = "INFO"
    debug: bool = False
    redact_logs: bool = True
    redis_url: str = "redis://localhost:6379/0"
    internal_api_port: int = 8081
    internal_api_host: str = "127.0.0.1"
    internal_api_secret: str = ""
    throttle_rate_limit: float = 0.7
    admin_alert_chat_id_allowlist: str = ""


settings = BotSettings()
