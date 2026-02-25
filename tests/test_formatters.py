"""Tests for StructuredJSONFormatter and HumanReadableFormatter."""

import json
import logging

import pytest

from fastapi_correlation import HumanReadableFormatter, StructuredJSONFormatter
from fastapi_correlation.context import clear_log_context, set_log_context
from fastapi_correlation.formatters import LOKI_MAX_LOG_SIZE_BYTES


@pytest.fixture(autouse=True)
def _clear_context() -> None:
    clear_log_context()


def make_record(msg: str = "hello", level: int = logging.INFO) -> logging.LogRecord:
    record = logging.LogRecord(
        name="test",
        level=level,
        pathname="test.py",
        lineno=1,
        msg=msg,
        args=(),
        exc_info=None,
    )
    return record


class TestStructuredJSONFormatter:
    def test_output_is_valid_json(self) -> None:
        formatter = StructuredJSONFormatter()
        result = formatter.format(make_record())
        data = json.loads(result)
        assert isinstance(data, dict)

    def test_required_fields_present(self) -> None:
        formatter = StructuredJSONFormatter()
        data = json.loads(formatter.format(make_record("test message")))
        assert data["message"] == "test message"
        assert data["level"] == "INFO"
        assert data["logger"] == "test"
        assert "timestamp" in data

    def test_timestamp_is_rfc3339_utc(self) -> None:
        formatter = StructuredJSONFormatter()
        data = json.loads(formatter.format(make_record()))
        ts = data["timestamp"]
        assert ts.endswith("Z")
        assert "T" in ts

    def test_context_fields_merged(self) -> None:
        set_log_context(user_id="alice", endpoint="/test")
        formatter = StructuredJSONFormatter()
        data = json.loads(formatter.format(make_record()))
        assert data["user_id"] == "alice"
        assert data["endpoint"] == "/test"

    def test_exception_info_included(self) -> None:
        formatter = StructuredJSONFormatter()
        try:
            raise ValueError("boom")
        except ValueError:
            import sys

            record = make_record("error occurred")
            record.exc_info = sys.exc_info()
            data = json.loads(formatter.format(record))
            assert "exception" in data
            assert "ValueError" in data["exception"]

    def test_oversized_message_is_truncated(self) -> None:
        formatter = StructuredJSONFormatter()
        big_msg = "x" * (LOKI_MAX_LOG_SIZE_BYTES + 5000)
        record = make_record(big_msg)
        result = formatter.format(record)
        assert len(result) <= LOKI_MAX_LOG_SIZE_BYTES + 500  # some overhead for JSON keys
        assert "[TRUNCATED]" in result

    def test_no_environment_field(self) -> None:
        # environment was intentionally dropped from the package
        formatter = StructuredJSONFormatter()
        data = json.loads(formatter.format(make_record()))
        assert "environment" not in data


class TestHumanReadableFormatter:
    def test_returns_string(self) -> None:
        formatter = HumanReadableFormatter()
        result = formatter.format(make_record())
        assert isinstance(result, str)

    def test_contains_message(self) -> None:
        formatter = HumanReadableFormatter()
        result = formatter.format(make_record("hello world"))
        assert "hello world" in result

    def test_contains_level(self) -> None:
        formatter = HumanReadableFormatter()
        result = formatter.format(make_record(level=logging.WARNING))
        assert "WARNING" in result

    def test_dash_when_no_correlation_id(self) -> None:
        formatter = HumanReadableFormatter()
        result = formatter.format(make_record())
        assert "[-]" in result
