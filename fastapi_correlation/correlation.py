"""
Correlation ID middleware for distributed tracing.

Extracts or generates a correlation ID per request, stores it in a ContextVar
so it's accessible anywhere in the call stack, and echoes it back in the
response as X-Correlation-ID.

Generated IDs are full UUID4 strings (36 chars). Incoming header values are
sanitised — only alphanumeric characters, hyphens, and underscores are kept,
capped at 36 chars — to prevent log injection while preserving interoperability
with upstream services that send their own IDs.
"""

import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

# Per-request correlation ID, stored in an async-safe ContextVar
correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")


class CorrelationIDMiddleware(BaseHTTPMiddleware):  # type: ignore[misc]
    """
    Middleware that attaches a correlation ID to every HTTP request.

    Behaviour:
    - If the incoming request contains an ``X-Correlation-ID`` header, its
      value is sanitised (alphanumeric, hyphens, underscores only; capped at
      36 chars) and used as the correlation ID.
    - If the header is absent or empty after sanitisation, a fresh UUID4 is
      generated.
    - The ID is stored in :data:`correlation_id` ContextVar so it is
      accessible anywhere in the request lifecycle via
      :func:`get_correlation_id`.
    - The ID is also stored in ``request.state.request_id`` for other
      middleware (e.g. audit logging).
    - The ID is added to the response as ``X-Correlation-ID``.

    Example::

        app.add_middleware(CorrelationIDMiddleware)
    """

    async def dispatch(self, request: Request, call_next: ASGIApp) -> Response:
        """
        Process the request and attach a correlation ID.

        Args:
            request: Incoming HTTP request.
            call_next: Next middleware or endpoint handler.

        Returns:
            Response with ``X-Correlation-ID`` header added.
        """
        incoming = request.headers.get("X-Correlation-ID", "").strip()
        safe = "".join(c for c in incoming if c.isalnum() or c in "-_")[:36]
        cid = safe if safe else str(uuid.uuid4())

        # Expose via request.state for other middleware
        request.state.request_id = cid

        # Expose via ContextVar for logging / handlers
        correlation_id.set(cid)

        response = await call_next(request)
        response.headers["X-Correlation-ID"] = cid
        return response


def get_correlation_id() -> str:
    """
    Return the correlation ID for the current request.

    Returns:
        Correlation ID string (full UUID4 or sanitised upstream value),
        or ``""`` if called outside a request context.

    Example::

        from fastapi_correlation import get_correlation_id

        cid = get_correlation_id()
        logger.info(f"Handling request {cid}")
    """
    return correlation_id.get()
