"""Tests for logslice.transformer."""

import pytest

from logslice.transformer import (
    TransformError,
    add_field,
    apply_field,
    drop_fields,
    rename_field,
)


ENTRIES = [
    {"level": "info", "msg": "started", "ts": 1},
    {"level": "error", "msg": "failed", "ts": 2},
]


class TestRenameField:
    def test_renames_existing_field(self):
        result = list(rename_field(ENTRIES, "msg", "message"))
        assert "message" in result[0]
        assert "msg" not in result[0]

    def test_missing_field_passes_through(self):
        result = list(rename_field(ENTRIES, "nonexistent", "x"))
        assert result[0] == ENTRIES[0]

    def test_does_not_mutate_original(self):
        original = {"a": 1}
        list(rename_field([original], "a", "b"))
        assert "a" in original


class TestDropFields:
    def test_drops_specified_fields(self):
        result = list(drop_fields(ENTRIES, ["ts"]))
        assert "ts" not in result[0]
        assert "level" in result[0]

    def test_missing_field_ignored(self):
        result = list(drop_fields(ENTRIES, ["nonexistent"]))
        assert result[0] == ENTRIES[0]

    def test_drop_multiple(self):
        result = list(drop_fields(ENTRIES, ["level", "ts"]))
        assert list(result[0].keys()) == ["msg"]


class TestAddField:
    def test_adds_new_field(self):
        result = list(add_field(ENTRIES, "env", "prod"))
        assert result[0]["env"] == "prod"

    def test_overwrites_by_default(self):
        result = list(add_field(ENTRIES, "level", "debug"))
        assert result[0]["level"] == "debug"

    def test_no_overwrite_preserves_existing(self):
        result = list(add_field(ENTRIES, "level", "debug", overwrite=False))
        assert result[0]["level"] == "info"

    def test_nested_key_created(self):
        result = list(add_field([{"a": 1}], "meta.env", "staging"))
        assert result[0]["meta"]["env"] == "staging"


class TestApplyField:
    def test_transforms_value(self):
        result = list(apply_field(ENTRIES, "level", str.upper))
        assert result[0]["level"] == "INFO"

    def test_missing_field_unchanged(self):
        result = list(apply_field(ENTRIES, "missing", str.upper))
        assert result[0] == ENTRIES[0]

    def test_raises_on_func_error(self):
        def boom(v):
            raise ValueError("oops")

        with pytest.raises(TransformError, match="oops"):
            list(apply_field(ENTRIES, "level", boom))
