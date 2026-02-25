"""Tests for set_log_context / get_log_context / clear_log_context."""

from fastapi_correlation import clear_log_context, get_log_context, set_log_context


def test_set_and_get_log_context() -> None:
    clear_log_context()
    set_log_context(user_id="alice", endpoint="/api/test")
    ctx = get_log_context()
    assert ctx["user_id"] == "alice"
    assert ctx["endpoint"] == "/api/test"


def test_set_log_context_merges_fields() -> None:
    clear_log_context()
    set_log_context(user_id="alice")
    set_log_context(status_code=200)
    ctx = get_log_context()
    assert ctx["user_id"] == "alice"
    assert ctx["status_code"] == 200


def test_clear_log_context_empties_dict() -> None:
    set_log_context(user_id="alice")
    clear_log_context()
    assert get_log_context() == {}


def test_get_log_context_returns_empty_dict_by_default() -> None:
    clear_log_context()
    assert get_log_context() == {}
