import logging
import os
import sys
from pathlib import Path
from typing import Any

import structlog

_CORRELATION_ID_KEYS = frozenset(
    {
        "telegram_id",
        "user_id",
        "owner_id",
        "file_id",
        "client_ip",
    }
)

_SENSITIVE_KEYS = frozenset(
    {
        "telegram_id",
        "user_id",
        "owner_id",
        "file_id",
        "token",
        "access_token",
        "client_ip",
    }
)

_FULL_REDACT_KEYS = frozenset(
    {
        "token",
        "access_token",
    }
)

_REDACT_ENABLED = False
_REDACT_IDENTIFIERS = True

_THIRD_PARTY = (
    "aiogram",
    "httpx",
    "httpcore",
    "aiohttp",
    "aiohttp.client",
    "aiohttp.web",
)


def _parse_log_level_name(name: str) -> int:
    key = (name or "WARNING").upper().strip()
    parsed = getattr(logging, key, None)
    if isinstance(parsed, int):
        return parsed
    return logging.WARNING


def _apply_third_party_log_levels(third_party_level: str) -> None:
    n = _parse_log_level_name(third_party_level)
    for lname in _THIRD_PARTY:
        logging.getLogger(lname).setLevel(n)


def _attach_dev_file_log(level: int, filename: str) -> None:
    raw = (os.environ.get("DOTSOUND_DEV_LOG_DIR") or "").strip()
    if not raw:
        return
    try:
        log_dir = Path(
            os.path.expanduser(os.path.expandvars(raw))
        ).resolve()
        log_dir.mkdir(parents=True, exist_ok=True)
        path = (log_dir / filename).resolve()
        base_s = str(path)
        root = logging.getLogger()
        for h in root.handlers:
            bfn = getattr(h, "baseFilename", None)
            if bfn and str(bfn) == base_s:
                return
        fh = logging.FileHandler(path, encoding="utf-8")
        fh.setLevel(level)
        fh.setFormatter(logging.Formatter("%(message)s"))
        root.addHandler(fh)
    except OSError:
        return


def _mask_value(key: str, value: Any) -> Any:
    if not _REDACT_ENABLED:
        return value
    lkey = key.lower()
    if lkey in _FULL_REDACT_KEYS:
        return "***REDACTED***"
    if lkey in _CORRELATION_ID_KEYS and not _REDACT_IDENTIFIERS:
        return value
    if lkey not in _SENSITIVE_KEYS:
        return value
    s = str(value)
    if len(s) <= 4:
        return "***"
    visible = max(2, len(s) // 5)
    return s[:visible] + "***" + s[-visible:]


def _redact_processor(
    logger: Any,
    method: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    if not _REDACT_ENABLED:
        return event_dict
    return {
        k: _mask_value(k, v)
        for k, v in event_dict.items()
    }


def configure_logging(
    log_level: str = "INFO",
    redact: bool = True,
    redact_identifiers: bool = True,
    json_output: bool = False,
    third_party_level: str = "WARNING",
) -> None:
    global _REDACT_ENABLED, _REDACT_IDENTIFIERS
    _REDACT_ENABLED = redact
    _REDACT_IDENTIFIERS = redact_identifiers if redact else True

    level = getattr(
        logging, log_level.upper(), logging.INFO
    )

    shared_processors: list[
        structlog.types.Processor
    ] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(
            fmt="iso", utc=True
        ),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        _redact_processor,
    ]

    if json_output:
        renderer: structlog.types.Processor = (
            structlog.processors.JSONRenderer()
        )
    else:
        renderer = structlog.dev.ConsoleRenderer(
            colors=True
        )

    structlog.configure(
        processors=shared_processors
        + [
            structlog.processors.format_exc_info,
            renderer,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        stream=sys.stdout,
        level=level,
        format="%(message)s",
    )
    _attach_dev_file_log(level, "bot.log")
    _apply_third_party_log_levels(third_party_level)
