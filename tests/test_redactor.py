"""Tests for logslice.redactor."""

import pytest

from logslice.redactor import (
    RedactionError,
    redact_fields,
    redact_pattern,
    redact_entries,
    _MASK,
)


class TestRedactFields:
    def test_single_field_masked(self):
        entry = {"user": "alice", "msg": "hello"}
        result = redact_fields(entry, ["user"])
        assert result["user"] == _MASK
        assert result["msg"] == "hello"

    def test_multiple_fields_masked(self):
        entry = {"email": "a@b.com", "token": "secret", "level": "info"}
        result = redact_fields(entry, ["email", "token"])
        assert result["email"] == _MASK
        assert result["token"] == _MASK
        assert result["level"] == "info"

    def test_missing_field_ignored(self):
        entry = {"msg": "hi"}
        result = redact_fields(entry, ["password"])
        assert result == {"msg": "hi"}

    def test_does_not_mutate_original(self):
        entry = {"user": "bob"}
        redact_fields(entry, ["user"])
        assert entry["user"] == "bob"

    def test_nested_field_masked(self):
        entry = {"auth": {"token": "abc123"}, "msg": "ok"}
        result = redact_fields(entry, ["auth.token"])
        assert result["auth"]["token"] == _MASK

    def test_custom_mask(self):
        entry = {"ssn": "123-45-6789"}
        result = redact_fields(entry, ["ssn"], mask="[HIDDEN]")
        assert result["ssn"] == "[HIDDEN]"


class TestRedactPattern:
    def test_replaces_pattern_in_field(self):
        entry = {"msg": "user email is test@example.com here"}
        result = redact_pattern(entry, "msg", r"[\w.+-]+@[\w-]+\.[\w.]+")
        assert "test@example.com" not in result["msg"]
        assert _MASK in result["msg"]

    def test_non_string_field_passes_through(self):
        entry = {"count": 42}
        result = redact_pattern(entry, "count", r"\d+")
        assert result["count"] == 42

    def test_missing_field_passes_through(self):
        entry = {"msg": "hello"}
        result = redact_pattern(entry, "token", r"\w+")
        assert result == {"msg": "hello"}

    def test_invalid_pattern_raises(self):
        entry = {"msg": "hello"}
        with pytest.raises(RedactionError):
            redact_pattern(entry, "msg", r"[invalid")

    def test_custom_replacement(self):
        entry = {"msg": "call 555-1234 now"}
        result = redact_pattern(entry, "msg", r"\d{3}-\d{4}", "[PHONE]")
        assert result["msg"] == "call [PHONE] now"


class TestRedactEntries:
    def test_redacts_stream_of_entries(self):
        entries = [
            {"user": "alice", "level": "info"},
            {"user": "bob", "level": "warn"},
        ]
        result = list(redact_entries(entries, fields=["user"]))
        assert all(e["user"] == _MASK for e in result)
        assert result[0]["level"] == "info"

    def test_pattern_applied_to_stream(self):
        entries = [{"msg": "token=abc123"}, {"msg": "token=xyz789"}]
        result = list(
            redact_entries(entries, pattern_field="msg", pattern=r"token=\w+")
        )
        assert all("token=" not in e["msg"] for e in result)

    def test_empty_stream_yields_nothing(self):
        result = list(redact_entries([], fields=["user"]))
        assert result == []

    def test_fields_and_pattern_combined(self):
        entries = [{"user": "carol", "msg": "ip=192.168.1.1"}]
        result = list(
            redact_entries(
                entries,
                fields=["user"],
                pattern_field="msg",
                pattern=r"\d+\.\d+\.\d+\.\d+",
                replacement="[IP]",
            )
        )
        assert result[0]["user"] == _MASK
        assert "[IP]" in result[0]["msg"]
