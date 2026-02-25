# fastapi-correlation

> 📢 **Hobby Project Notice:** This is a research and learning project exploring FastAPI
> middleware and structured logging best practices. Feel free to use it as a reference,
> report issues, or suggest improvements! Contributions and feedback are always welcome.

Correlation ID middleware and structured logging for FastAPI — zero project-specific
dependencies (only Starlette).

## Features

- `CorrelationIDMiddleware` — injects a unique `X-Correlation-ID` header per request
  (reads the incoming header if present, generates a UUID4 otherwise)
- `get_correlation_id()` — context-var accessor usable anywhere in the request lifecycle
- `LoggingContextMiddleware` — injects `endpoint`, `method`, `status_code`, and `user_id`
  into every log record for the duration of the request
- `set_log_context` / `get_log_context` / `clear_log_context` — helpers for enriching
  per-request structured log fields
- `StructuredJSONFormatter` — RFC 3339 UTC JSON output ready for Loki / Grafana Alloy
- `HumanReadableFormatter` — compact, coloured output for local development

## Installation

```bash
pip install fastapi-correlation
```

## Quick start

```python
from fastapi import FastAPI
from fastapi_correlation import (
    CorrelationIDMiddleware,
    LoggingContextMiddleware,
    StructuredJSONFormatter,
    set_log_context,
    get_correlation_id,
)
import logging, sys

# Wire up structured JSON logging
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(StructuredJSONFormatter())
logging.getLogger().addHandler(handler)

app = FastAPI()
app.add_middleware(LoggingContextMiddleware)
app.add_middleware(CorrelationIDMiddleware)

@app.get("/ping")
async def ping():
    set_log_context(custom_field="hello")
    return {"correlation_id": get_correlation_id()}
```

## License

MIT
