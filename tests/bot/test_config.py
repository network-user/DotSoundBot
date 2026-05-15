import pytest
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


def test_internal_api_host_loopback_default() -> None:
    env = {
        "BOT_TOKEN": "t",
        "BACKEND_BASE_URL": "http://b",
        "MINI_APP_URL": "http://m",
    }
    with patch.dict("os.environ", env, clear=True):
        s = BotSettings(_env_file=None)  # type: ignore[call-arg]

    assert s.internal_api_host == "127.0.0.1"
    assert s.internal_api_compose_bind is False


def test_internal_api_compose_bind_allows_all_interfaces() -> None:
    env = {
        "BOT_TOKEN": "t",
        "BACKEND_BASE_URL": "http://b",
        "MINI_APP_URL": "http://m",
        "INTERNAL_API_COMPOSE_BIND": "true",
        "INTERNAL_API_HOST": "0.0.0.0",
    }
    with patch.dict("os.environ", env, clear=True):
        s = BotSettings(_env_file=None)  # type: ignore[call-arg]

    assert s.internal_api_host == "0.0.0.0"
    assert s.internal_api_compose_bind is True


def test_internal_api_host_non_loopback_without_compose_bind_fails() -> None:
    env = {
        "BOT_TOKEN": "t",
        "BACKEND_BASE_URL": "http://b",
        "MINI_APP_URL": "http://m",
        "INTERNAL_API_HOST": "0.0.0.0",
    }
    with patch.dict("os.environ", env, clear=True):
        with pytest.raises(ValueError, match="loopback"):
            BotSettings(_env_file=None)  # type: ignore[call-arg]
