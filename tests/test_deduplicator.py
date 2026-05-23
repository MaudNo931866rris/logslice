"""Tests for logslice.deduplicator."""

import pytest

from logslice.deduplicator import (
    DeduplicationError,
    _entry_fingerprint,
    deduplicate,
)


# ---------------------------------------------------------------------------
# _entry_fingerprint
# ---------------------------------------------------------------------------

class TestEntryFingerprint:
    def test_same_entry_same_hash(self):
        e = {"level": "info", "msg": "hello"}
        assert _entry_fingerprint(e) == _entry_fingerprint(e)

    def test_different_entries_different_hash(self):
        a = {"msg": "hello"}
        b = {"msg": "world"}
        assert _entry_fingerprint(a) != _entry_fingerprint(b)

    def test_field_subset_ignores_other_keys(self):
        a = {"msg": "hello", "ts": "2024-01-01"}
        b = {"msg": "hello", "ts": "2024-01-02"}
        assert _entry_fingerprint(a, fields=["msg"]) == _entry_fingerprint(b, fields=["msg"])

    def test_field_subset_detects_difference(self):
        a = {"msg": "hello", "ts": "2024-01-01"}
        b = {"msg": "world", "ts": "2024-01-01"}
        assert _entry_fingerprint(a, fields=["msg"]) != _entry_fingerprint(b, fields=["msg"])

    def test_missing_field_treated_as_none(self):
        a = {"msg": "hi"}
        b = {"msg": "hi", "level": None}
        # Both produce None for "level" in subset
        assert _entry_fingerprint(a, fields=["msg", "level"]) == _entry_fingerprint(
            b, fields=["msg", "level"]
        )


# ---------------------------------------------------------------------------
# deduplicate
# ---------------------------------------------------------------------------

class TestDeduplicate:
    def test_no_duplicates_passes_all(self):
        entries = [{"id": 1}, {"id": 2}, {"id": 3}]
        assert list(deduplicate(entries)) == entries

    def test_exact_duplicates_removed(self):
        entries = [{"msg": "a"}, {"msg": "a"}, {"msg": "b"}]
        assert list(deduplicate(entries)) == [{"msg": "a"}, {"msg": "b"}]

    def test_field_based_dedup(self):
        entries = [
            {"msg": "a", "ts": 1},
            {"msg": "a", "ts": 2},
            {"msg": "b", "ts": 3},
        ]
        result = list(deduplicate(entries, fields=["msg"]))
        assert len(result) == 2
        assert result[0]["ts"] == 1
        assert result[1]["msg"] == "b"

    def test_window_allows_repeat_after_eviction(self):
        entries = [{"msg": "a"}, {"msg": "b"}, {"msg": "a"}]
        # window=1: after seeing "b", "a" is evicted from seen
        result = list(deduplicate(entries, window=1))
        assert result == [{"msg": "a"}, {"msg": "b"}, {"msg": "a"}]

    def test_window_zero_raises(self):
        with pytest.raises(DeduplicationError):
            list(deduplicate([], window=0))

    def test_empty_input(self):
        assert list(deduplicate([])) == []

    def test_global_dedup_across_many(self):
        entries = [{"x": i % 3} for i in range(9)]
        result = list(deduplicate(entries))
        assert len(result) == 3
