"""
Structured logging formatters.

Provides two formatters:

- :class:`StructuredJSONFormatter` — RFC3339 UTC JSON output for
  Loki / Grafana Alloy ingestion.
- :class:`HumanReadableFormatter` — coloured, human-friendly output for
  local development.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any

# Maximum log size in bytes before the message is truncated.
# Prevents oversized entries from being rejected by Loki (default 100 KB).
LOKI_MAX_LOG_SIZE_BYTES: int = 102400


def _get_correlation_id() -> str:
    """Return the current correlation ID, or empty string if unavailable."""
    try:
        from fastapi_correlation.correlation import get_correlation_id

        return get_correlation_id()
    except Exception:  # noqa: BLE001
        return ""


def _get_log_context() -> dict[str, Any]:
    """Return the current log context dict, or empty dict if unavailable."""
    try:
        from fastapi_correlation.context import get_log_context

        return get_log_context()
    except Exception:  # noqa: BLE001
        return {}


class StructuredJSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging compatible with Loki / Grafana Alloy.

    Output fields per log record:

    - ``timestamp`` — RFC3339 UTC (e.g. ``2026-02-25T13:27:15.699Z``)
    - ``level`` — ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``, ``CRITICAL``
    - ``logger`` — logger name (``root`` if using the root logger)
    - ``message`` — formatted log message
    - ``module``, ``function``, ``line`` — source location
    - ``request_id`` — correlation ID if set via :class:`CorrelationIDMiddleware`
    - Any extra fields set via :func:`set_log_context`
    - ``exception`` — formatted traceback when ``exc_info`` is present

    Log messages longer than :data:`LOKI_MAX_LOG_SIZE_BYTES` are truncated.

    Example::

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredJSONFormatter())
        logging.getLogger().addHandler(handler)
    """

    # Fields that are part of the LogRecord internals — skip them when adding extras
    _SKIP_FIELDS: frozenset[str] = frozenset(
        [
            "name",
            "msg",
            "args",
            "created",
            "filename",
            "funcName",
            "levelname",
            "levelno",
            "lineno",
            "module",
            "msecs",
            "message",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "thread",
            "threadName",
            "exc_info",
            "exc_text",
            "stack_info",
            "taskName",
        ]
    )

    def format(self, record: logging.LogRecord) -> str:
        """
        Format *record* as a JSON string.

        Args:
            record: The log record to format.

        Returns:
            JSON string ready for stdout / file handler output.
        """
        log_data: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%S."
            )
            + f"{record.msecs:03.0f}Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Attach correlation ID when available
        cid = _get_correlation_id()
        if cid:
            log_data["request_id"] = cid

        # Merge per-request context fields (user_id, endpoint, …)
        context = _get_log_context()
        if context:
            log_data.update(context)

        # Attach exception traceback when present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Attach any extra fields added via logger.info(…, extra={…})
        for key, value in record.__dict__.items():
            if key not in self._SKIP_FIELDS:
                try:
                    json.dumps(value)
                    log_data[key] = value
                except (TypeError, ValueError):
                    log_data[key] = str(value)

        json_str = json.dumps(log_data)

        # Truncate oversized messages to stay within Loki limits
        if len(json_str) > LOKI_MAX_LOG_SIZE_BYTES:
            message = log_data.get("message", "")
            if isinstance(message, str):
                log_data["message"] = (
                    message[: LOKI_MAX_LOG_SIZE_BYTES - 1000] + "... [TRUNCATED]"
                )
            json_str = json.dumps(log_data)

        return json_str


class HumanReadableFormatter(logging.Formatter):
    """
    Human-friendly formatter for local development.

    Uses a compact format for INFO and a more verbose format (with module,
    function, and line number) for DEBUG / WARNING / ERROR.  The current
    correlation ID is injected as ``[<cid>]`` so it is visible at a glance.

    Example::

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(HumanReadableFormatter())
        logging.getLogger().addHandler(handler)
    """

    INFO_FMT = "%(asctime)s - [%(correlation_id)s] %(levelname)s: %(message)s"
    VERBOSE_FMT = "%(asctime)s - [%(correlation_id)s] %(levelname)s: %(module)s.%(funcName)s:%(lineno)d - %(message)s"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialise the formatter."""
        super().__init__(*args, **kwargs)
        self._formatters = {
            logging.INFO: logging.Formatter(self.INFO_FMT, datefmt="%Y-%m-%d %H:%M:%S"),
            logging.WARNING: logging.Formatter(self.VERBOSE_FMT, datefmt="%Y-%m-%d %H:%M:%S"),
            logging.ERROR: logging.Formatter(self.VERBOSE_FMT, datefmt="%Y-%m-%d %H:%M:%S"),
            logging.DEBUG: logging.Formatter(self.VERBOSE_FMT, datefmt="%Y-%m-%d %H:%M:%S"),
        }

    def format(self, record: logging.LogRecord) -> str:
        """
        Format *record* with the correlation ID injected.

        Args:
            record: The log record to format.

        Returns:
            Formatted log string.
        """
        record.correlation_id = _get_correlation_id() or "-"  # type: ignore[attr-defined]
        formatter = self._formatters.get(record.levelno, self._formatters[logging.INFO])
        return formatter.format(record)
