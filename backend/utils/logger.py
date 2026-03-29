"""
ARIA Structured Logger
Outputs JSON-formatted log lines. Supports structured kwargs via `extra` dict.
Usage: logger.info("msg", extra={"key": "value"}) or logger.info("msg", **{"key": "value"})
       Use the aria_log() helper for the cleaner logger.info("msg", key=val) syntax.
"""
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any


class JsonFormatter(logging.Formatter):
    """Format log records as single-line JSON strings."""

    _SKIP_KEYS = frozenset({
        "name", "msg", "args", "levelname", "levelno", "pathname",
        "filename", "module", "exc_info", "exc_text", "stack_info",
        "lineno", "funcName", "created", "msecs", "relativeCreated",
        "thread", "threadName", "processName", "process", "message",
        "taskName",
    })

    def format(self, record: logging.LogRecord) -> str:
        obj: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            obj["exc"] = self.formatException(record.exc_info)
        # Merge any extra fields (passed via extra={} or through _aria_extra)
        for key, value in record.__dict__.items():
            if key not in self._SKIP_KEYS and not key.startswith("_"):
                obj[key] = value
        return json.dumps(obj, default=str)


class AriaLogger:
    """
    Thin wrapper around stdlib logger that supports structured kwargs.
    Usage: logger.info("Navigation done", url=url, task_id=task_id)
    """

    def __init__(self, name: str) -> None:
        self._logger = logging.getLogger(name)
        if not self._logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(JsonFormatter())
            self._logger.addHandler(handler)
            self._logger.setLevel(logging.DEBUG)
            self._logger.propagate = False

    def _log(self, level: int, msg: str, **kwargs: Any) -> None:
        if self._logger.isEnabledFor(level):
            extra = {k: v for k, v in kwargs.items() if k != "exc_info"}
            exc_info = kwargs.get("exc_info", False)
            self._logger.log(level, msg, extra=extra, exc_info=exc_info)

    def debug(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.DEBUG, msg, **kwargs)

    def info(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.INFO, msg, **kwargs)

    def warning(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.WARNING, msg, **kwargs)

    def error(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.ERROR, msg, **kwargs)

    def critical(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.CRITICAL, msg, **kwargs)


def get_logger(name: str) -> "AriaLogger":
    """Get a named structured logger for ARIA."""
    return AriaLogger(name)
