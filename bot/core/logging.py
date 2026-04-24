import logging
import os
import sys
from pathlib import Path
from typing import Any

import structlog

_SENSITIVE_KEYS = frozenset({
    "telegram_id",
    "user_id",
    "owner_id",
    "file_id",
    "token",
    "access_token",
    "client_ip",
})

_REDACT_ENABLED = False


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
    if key not in _SENSITIVE_KEYS:
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
    json_output: bool = False,
) -> None:
    global _REDACT_ENABLED
    _REDACT_ENABLED = redact

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

    for noisy in ("aiogram", "httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(
            logging.WARNING
        )
