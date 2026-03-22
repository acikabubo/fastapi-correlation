"""Tests for set_log_context / get_log_context / clear_log_context."""

import asyncio

from fastapi_correlation import clear_log_context, get_log_context, set_log_context
from fastapi_correlation.context import log_context


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


def test_get_log_context_before_any_set_returns_empty_dict() -> None:
    """default=None path: get_log_context() must return {} even with no prior set."""
    log_context.set(None)
    assert get_log_context() == {}


async def test_set_log_context_concurrent_tasks_are_isolated() -> None:
    """Regression test for race condition: concurrent tasks must not bleed context."""
    results: dict[str, str] = {}

    async def task_a() -> None:
        clear_log_context()
        set_log_context(user_id="alice")
        await asyncio.sleep(0)  # yield — allow task_b to run
        results["a"] = get_log_context().get("user_id", "")

    async def task_b() -> None:
        clear_log_context()
        set_log_context(user_id="bob")
        await asyncio.sleep(0)
        results["b"] = get_log_context().get("user_id", "")

    await asyncio.gather(
        asyncio.create_task(task_a()),
        asyncio.create_task(task_b()),
    )

    assert results["a"] == "alice", f"Task A saw '{results['a']}' — context bleed!"
    assert results["b"] == "bob", f"Task B saw '{results['b']}' — context bleed!"


async def test_clear_log_context_does_not_affect_other_tasks() -> None:
    """Clearing context in one task must not wipe another task's context."""
    other_saw: dict[str, str] = {}

    async def task_setter() -> None:
        set_log_context(user_id="alice")
        await asyncio.sleep(0)
        other_saw["value"] = get_log_context().get("user_id", "")

    async def task_clearer() -> None:
        await asyncio.sleep(0)  # let setter run first
        clear_log_context()

    await asyncio.gather(
        asyncio.create_task(task_setter()),
        asyncio.create_task(task_clearer()),
    )

    assert other_saw["value"] == "alice", (
        f"task_clearer wiped task_setter's context — got '{other_saw['value']}'"
    )
