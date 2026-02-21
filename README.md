# fastapi-correlation

> **Name reserved — active development coming soon.**

Correlation ID middleware and structured logging for FastAPI.

## Planned Features

- `CorrelationMiddleware` — injects a unique `X-Correlation-ID` header per request (generates one if absent)
- `get_correlation_id()` — context-var accessor usable anywhere in the request lifecycle
- Structured logging integration — automatically attaches `correlation_id` to every log record
- WebSocket support — propagates correlation ID through WebSocket connections
- Zero project-specific dependencies (only Starlette/FastAPI)

## Status

This package is a name reservation. Implementation will follow.

Follow progress at: https://github.com/acikabubo/fastapi-correlation

## License

MIT
