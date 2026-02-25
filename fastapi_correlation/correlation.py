"""
Correlation ID middleware for distributed tracing.

Extracts or generates an 8-character correlation ID per request, stores it in
a ContextVar so it's accessible anywhere in the call stack, and echoes it back
in the response as X-Correlation-ID.
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
    - If the incoming request contains an ``X-Correlation-ID`` header its
      value (truncated to 8 characters) is used as-is.
    - Otherwise a new 8-character UUID fragment is generated.
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
        cid = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))[:8]

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
        8-character correlation ID string, or ``""`` if called outside a
        request context.

    Example::

        from fastapi_correlation import get_correlation_id

        cid = get_correlation_id()
        logger.info(f"Handling request {cid}")
    """
    return correlation_id.get()
