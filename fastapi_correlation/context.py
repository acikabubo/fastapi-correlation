"""
Async-safe log context for structured logging.

Provides ContextVar-based storage for per-request fields (user_id, endpoint,
method, status_code, etc.) that are merged into every log record by
StructuredJSONFormatter.
"""

from contextvars import ContextVar
from typing import Any

# Per-request context dict, stored in an async-safe ContextVar.
# Default is None (not {}) to avoid a shared mutable object across all contexts.
log_context: ContextVar[dict[str, Any] | None] = ContextVar("log_context", default=None)


def set_log_context(**kwargs: Any) -> None:
    """
    Add or update fields in the current request's log context.

    Fields are merged into every log record emitted by StructuredJSONFormatter
    for the duration of the current request.

    Always creates a new dict — never mutates the stored dict. This is safe to
    call from concurrent async tasks; each task has its own isolated context.

    Args:
        **kwargs: Key-value pairs to add (e.g. user_id="alice", status_code=200).

    Example:
        >>> set_log_context(user_id="alice", endpoint="/api/authors")
        >>> logger.info("Processing request")  # includes user_id and endpoint
    """
    current = {**(log_context.get() or {}), **kwargs}
    log_context.set(current)


def get_log_context() -> dict[str, Any]:
    """
    Return a shallow copy of the current request's log context.

    Returns a copy so callers cannot accidentally mutate the stored context.

    Returns:
        Dictionary of contextual log fields.
    """
    return dict(log_context.get() or {})


def clear_log_context() -> None:
    """Clear the log context (call at end of each request)."""
    log_context.set({})
