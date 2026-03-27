from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    bot_token: str
    backend_base_url: str
    log_level: str = "INFO"


settings = BotSettings()
