"""Tests for CorrelationIDMiddleware and get_correlation_id."""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from fastapi_correlation import CorrelationIDMiddleware, get_correlation_id


@pytest.fixture()
def app() -> FastAPI:
    """FastAPI app with CorrelationIDMiddleware and a test endpoint."""
    _app = FastAPI()
    _app.add_middleware(CorrelationIDMiddleware)

    @_app.get("/")
    async def root(request: Request) -> PlainTextResponse:
        return PlainTextResponse(get_correlation_id())

    return _app


@pytest.mark.asyncio
async def test_generates_correlation_id_when_header_absent(app: FastAPI) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")

    assert response.status_code == 200
    cid = response.headers["x-correlation-id"]
    assert len(cid) == 8
    assert response.text == cid


@pytest.mark.asyncio
async def test_uses_provided_correlation_id(app: FastAPI) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/", headers={"X-Correlation-ID": "abc12345xyz"})

    assert response.status_code == 200
    # Truncated to 8 chars
    assert response.headers["x-correlation-id"] == "abc12345"
    assert response.text == "abc12345"


@pytest.mark.asyncio
async def test_echoes_correlation_id_in_response_header(app: FastAPI) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/", headers={"X-Correlation-ID": "deadbeef"})

    assert response.headers["x-correlation-id"] == "deadbeef"


def test_get_correlation_id_returns_empty_outside_request() -> None:
    # Outside a request context the ContextVar default is ""
    assert get_correlation_id() == ""
