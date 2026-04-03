"""Tests for LoggingContextMiddleware."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response

from fastapi_correlation import LoggingContextMiddleware


@pytest.fixture()
def app() -> FastAPI:
    return FastAPI()


def make_request(path: str = "/api/test", method: str = "GET", user: object = None) -> Request:
    mock = MagicMock(spec=Request)
    mock.url.path = path
    mock.method = method
    mock.scope = {"user": user} if user is not None else {}
    if user is not None:
        mock.user = user
    return mock  # type: ignore[return-value]


@pytest.mark.asyncio
async def test_sets_endpoint_and_method(app: FastAPI) -> None:
    middleware = LoggingContextMiddleware(app)
    request = make_request()
    call_next = AsyncMock(return_value=Response(status_code=200))

    with patch("fastapi_correlation.context_middleware.set_log_context") as mock_set:
        await middleware.dispatch(request, call_next)

    calls = {k: v for call in mock_set.call_args_list for k, v in call[1].items()}
    assert calls["endpoint"] == "/api/test"
    assert calls["method"] == "GET"


@pytest.mark.asyncio
async def test_sets_user_id_from_authenticated_user(app: FastAPI) -> None:
    middleware = LoggingContextMiddleware(app)
    user = MagicMock()
    user.username = "alice"
    request = make_request(user=user)
    call_next = AsyncMock(return_value=Response(status_code=200))

    with patch("fastapi_correlation.context_middleware.set_log_context") as mock_set:
        await middleware.dispatch(request, call_next)

    calls = {k: v for call in mock_set.call_args_list for k, v in call[1].items()}
    assert calls.get("user_id") == "alice"


@pytest.mark.asyncio
async def test_no_user_id_without_authenticated_user(app: FastAPI) -> None:
    middleware = LoggingContextMiddleware(app)
    request = make_request()
    call_next = AsyncMock(return_value=Response(status_code=200))

    with patch("fastapi_correlation.context_middleware.set_log_context") as mock_set:
        await middleware.dispatch(request, call_next)

    calls = {k: v for call in mock_set.call_args_list for k, v in call[1].items()}
    assert "user_id" not in calls


@pytest.mark.asyncio
async def test_sets_status_code(app: FastAPI) -> None:
    middleware = LoggingContextMiddleware(app)
    request = make_request()
    call_next = AsyncMock(return_value=Response(status_code=404))

    with patch("fastapi_correlation.context_middleware.set_log_context") as mock_set:
        await middleware.dispatch(request, call_next)

    calls = {k: v for call in mock_set.call_args_list for k, v in call[1].items()}
    assert calls["status_code"] == 404


@pytest.mark.asyncio
async def test_clears_context_after_request(app: FastAPI) -> None:
    middleware = LoggingContextMiddleware(app)
    request = make_request()
    call_next = AsyncMock(return_value=Response(status_code=200))

    with patch("fastapi_correlation.context_middleware.clear_log_context") as mock_clear:
        await middleware.dispatch(request, call_next)

    mock_clear.assert_called_once()


@pytest.mark.asyncio
async def test_clears_context_even_when_call_next_raises(app: FastAPI) -> None:
    middleware = LoggingContextMiddleware(app)
    request = make_request()
    call_next = AsyncMock(side_effect=RuntimeError("handler crashed"))

    with patch("fastapi_correlation.context_middleware.clear_log_context") as mock_clear:
        with pytest.raises(RuntimeError):
            await middleware.dispatch(request, call_next)

    mock_clear.assert_called_once()


@pytest.mark.asyncio
async def test_clears_context_even_when_post_response_logic_raises(app: FastAPI) -> None:
    middleware = LoggingContextMiddleware(app)
    request = make_request()
    call_next = AsyncMock(return_value=Response(status_code=200))

    with patch("fastapi_correlation.context_middleware.clear_log_context") as mock_clear:
        with patch(
            "fastapi_correlation.context_middleware.set_log_context",
            side_effect=[None, RuntimeError("set failed")],
        ):
            with pytest.raises(RuntimeError):
                await middleware.dispatch(request, call_next)

    mock_clear.assert_called_once()
