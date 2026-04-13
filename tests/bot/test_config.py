from unittest.mock import patch

from bot.config import BotSettings


def test_defaults_applied() -> None:
    env = {
        "BOT_TOKEN": "tok",
        "BACKEND_BASE_URL": "http://localhost:8000",
        "MINI_APP_URL": "http://localhost:5173",
    }
    with patch.dict("os.environ", env, clear=True):
        s = BotSettings(
            _env_file=None,  # type: ignore[call-arg]
        )

    assert s.log_level == "INFO"
    assert s.debug is False
    assert s.redact_logs is True
    assert s.redis_url == "redis://localhost:6379/0"
    assert s.internal_api_port == 8081
    assert s.internal_api_secret == ""


def test_env_override() -> None:
    env = {
        "BOT_TOKEN": "test-token",
        "BACKEND_BASE_URL": "http://api:9000",
        "MINI_APP_URL": "https://app.example.com",
        "LOG_LEVEL": "DEBUG",
        "DEBUG": "true",
        "REDIS_URL": "redis://r:6379/1",
        "INTERNAL_API_PORT": "9090",
        "INTERNAL_API_SECRET": "s3cret",
    }
    with patch.dict("os.environ", env, clear=True):
        s = BotSettings(
            _env_file=None,  # type: ignore[call-arg]
        )

    assert s.bot_token == "test-token"
    assert s.backend_base_url == "http://api:9000"
    assert s.log_level == "DEBUG"
    assert s.debug is True
    assert s.redis_url == "redis://r:6379/1"
    assert s.internal_api_port == 9090
    assert s.internal_api_secret == "s3cret"


def test_required_fields_present() -> None:
    env = {
        "BOT_TOKEN": "t",
        "BACKEND_BASE_URL": "http://b",
        "MINI_APP_URL": "http://m",
    }
    with patch.dict("os.environ", env, clear=True):
        s = BotSettings(
            _env_file=None,  # type: ignore[call-arg]
        )

    assert s.bot_token == "t"
    assert s.backend_base_url == "http://b"
    assert s.mini_app_url == "http://m"
