"""fastapi-correlation — Correlation ID middleware and structured logging for FastAPI."""

from fastapi_correlation.context import clear_log_context, get_log_context, set_log_context
from fastapi_correlation.context_middleware import LoggingContextMiddleware
from fastapi_correlation.correlation import CorrelationIDMiddleware, get_correlation_id
from fastapi_correlation.formatters import HumanReadableFormatter, StructuredJSONFormatter

__version__ = "0.0.1"

__all__ = [
    # Middleware
    "CorrelationIDMiddleware",
    "LoggingContextMiddleware",
    # Log context helpers
    "set_log_context",
    "get_log_context",
    "clear_log_context",
    # Formatters
    "StructuredJSONFormatter",
    "HumanReadableFormatter",
    # Utilities
    "get_correlation_id",
]
