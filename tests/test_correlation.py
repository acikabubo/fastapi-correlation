"""Tests for CorrelationIDMiddleware and get_correlation_id."""

import re
import uuid

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


_UUID4_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


@pytest.mark.asyncio
async def test_generates_correlation_id_when_header_absent(app: FastAPI) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")

    assert response.status_code == 200
    cid = response.headers["x-correlation-id"]
    assert _UUID4_RE.match(cid), f"Expected UUID4, got: {cid!r}"
    assert response.text == cid


@pytest.mark.asyncio
async def test_generated_id_is_full_uuid4(app: FastAPI) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")

    cid = response.headers["x-correlation-id"]
    # Must be parseable as a valid UUID4
    parsed = uuid.UUID(cid, version=4)
    assert str(parsed) == cid


@pytest.mark.asyncio
async def test_uses_provided_correlation_id(app: FastAPI) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/", headers={"X-Correlation-ID": "abc-12345"})

    assert response.status_code == 200
    assert response.headers["x-correlation-id"] == "abc-12345"
    assert response.text == "abc-12345"


@pytest.mark.asyncio
async def test_echoes_correlation_id_in_response_header(app: FastAPI) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/", headers={"X-Correlation-ID": "deadbeef"})

    assert response.headers["x-correlation-id"] == "deadbeef"


@pytest.mark.asyncio
async def test_sanitises_unsafe_chars_in_incoming_header(app: FastAPI) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/", headers={"X-Correlation-ID": "abc!@#def"})

    # Only alphanumeric chars survive sanitisation
    assert response.headers["x-correlation-id"] == "abcdef"


@pytest.mark.asyncio
async def test_empty_after_sanitisation_falls_back_to_uuid(app: FastAPI) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/", headers={"X-Correlation-ID": "!@#$%^"})

    cid = response.headers["x-correlation-id"]
    assert _UUID4_RE.match(cid), f"Expected UUID4 fallback, got: {cid!r}"


@pytest.mark.asyncio
async def test_caps_incoming_header_at_36_chars(app: FastAPI) -> None:
    long_id = "a" * 50
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/", headers={"X-Correlation-ID": long_id})

    assert len(response.headers["x-correlation-id"]) == 36


def test_get_correlation_id_returns_empty_outside_request() -> None:
    # Outside a request context the ContextVar default is ""
    assert get_correlation_id() == ""
