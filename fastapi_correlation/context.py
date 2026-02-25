"""
Async-safe log context for structured logging.

Provides ContextVar-based storage for per-request fields (user_id, endpoint,
method, status_code, etc.) that are merged into every log record by
StructuredJSONFormatter.
"""

from contextvars import ContextVar
from typing import Any

# Per-request context dict, stored in an async-safe ContextVar
log_context: ContextVar[dict[str, Any]] = ContextVar("log_context", default={})


def set_log_context(**kwargs: Any) -> None:
    """
    Add or update fields in the current request's log context.

    Fields are merged into every log record emitted by StructuredJSONFormatter
    for the duration of the current request.

    Args:
        **kwargs: Key-value pairs to add (e.g. user_id="alice", status_code=200).

    Example:
        >>> set_log_context(user_id="alice", endpoint="/api/authors")
        >>> logger.info("Processing request")  # includes user_id and endpoint
    """
    current = log_context.get()
    current.update(kwargs)
    log_context.set(current)


def get_log_context() -> dict[str, Any]:
    """
    Return the current request's log context.

    Returns:
        Dictionary of contextual log fields.
    """
    return log_context.get()


def clear_log_context() -> None:
    """Clear the log context (call at end of each request)."""
    log_context.set({})
