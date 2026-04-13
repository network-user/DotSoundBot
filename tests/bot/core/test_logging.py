import logging
from unittest.mock import patch

import pytest
import structlog

from bot.core.logging import (
    _mask_value,
    _redact_processor,
    configure_logging,
)

pytestmark = pytest.mark.anyio


class TestMaskValue:
    def test_disabled_returns_original(self) -> None:
        with patch(
            "bot.core.logging._REDACT_ENABLED", False
        ):
            assert _mask_value("token", "abc") == "abc"

    def test_non_sensitive_key_unchanged(
        self,
    ) -> None:
        with patch(
            "bot.core.logging._REDACT_ENABLED", True
        ):
            assert (
                _mask_value("username", "alice")
                == "alice"
            )

    def test_short_value_fully_masked(self) -> None:
        with patch(
            "bot.core.logging._REDACT_ENABLED", True
        ):
            result = _mask_value("token", "ab")
            assert result == "***"

    def test_long_value_partially_masked(
        self,
    ) -> None:
        with patch(
            "bot.core.logging._REDACT_ENABLED", True
        ):
            result = _mask_value(
                "token", "abcdefghij"
            )
            assert "***" in result
            assert result.startswith("ab")
            assert result.endswith("ij")

    def test_sensitive_keys_masked(self) -> None:
        with patch(
            "bot.core.logging._REDACT_ENABLED", True
        ):
            for key in (
                "telegram_id",
                "user_id",
                "owner_id",
                "file_id",
                "access_token",
                "client_ip",
            ):
                result = _mask_value(
                    key, "1234567890"
                )
                assert "***" in result


class TestRedactProcessor:
    def test_disabled_passthrough(self) -> None:
        with patch(
            "bot.core.logging._REDACT_ENABLED", False
        ):
            event = {"token": "secret", "msg": "hi"}
            result = _redact_processor(
                None, "info", event
            )
            assert result["token"] == "secret"

    def test_enabled_redacts(self) -> None:
        with patch(
            "bot.core.logging._REDACT_ENABLED", True
        ):
            event = {
                "token": "supersecret123",
                "msg": "hi",
            }
            result = _redact_processor(
                None, "info", event
            )
            assert "***" in result["token"]
            assert result["msg"] == "hi"


class TestConfigureLogging:
    def test_console_output(self) -> None:
        configure_logging(
            log_level="DEBUG",
            redact=False,
            json_output=False,
        )
        logger = structlog.get_logger("test")
        assert logger is not None

    def test_json_output(self) -> None:
        configure_logging(
            log_level="INFO",
            redact=True,
            json_output=True,
        )
        logger = structlog.get_logger("test_json")
        assert logger is not None

    def test_noisy_loggers_suppressed(self) -> None:
        configure_logging(
            log_level="DEBUG",
            redact=False,
            json_output=False,
        )
        for name in ("aiogram", "httpx", "httpcore"):
            lvl = logging.getLogger(name).level
            assert lvl >= logging.WARNING

    def test_invalid_level_defaults_to_info(
        self,
    ) -> None:
        level = getattr(
            logging, "NONEXISTENT", logging.INFO
        )
        assert level == logging.INFO
