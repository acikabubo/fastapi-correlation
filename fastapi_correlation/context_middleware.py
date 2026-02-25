"""
Logging context middleware.

Injects per-request fields (endpoint, method, user_id, status_code) into the
log context so every log line emitted during the request automatically carries
them.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from fastapi_correlation.context import clear_log_context, set_log_context


class LoggingContextMiddleware(BaseHTTPMiddleware):  # type: ignore[misc]
    """
    Middleware that injects contextual fields into structured logs.

    Sets ``endpoint`` and ``method`` before the request is processed, then
    adds ``user_id`` (from ``request.user.username`` if Starlette
    ``AuthenticationMiddleware`` is installed) and ``status_code`` after the
    response is produced.  Clears the context once the response is sent.

    Example::

        app.add_middleware(LoggingContextMiddleware)
    """

    async def dispatch(self, request: Request, call_next: ASGIApp) -> Response:
        """
        Process the request and inject logging context.

        Args:
            request: Incoming HTTP request.
            call_next: Next middleware or endpoint handler.

        Returns:
            Response from the endpoint.
        """
        set_log_context(
            endpoint=request.url.path,
            method=request.method,
        )

        response = await call_next(request)

        # user is only available after AuthenticationMiddleware runs (inside call_next)
        if "user" in request.scope:
            user = request.user
            if hasattr(user, "username") and user.username:
                set_log_context(user_id=user.username)

        set_log_context(status_code=response.status_code)
        clear_log_context()

        return response
