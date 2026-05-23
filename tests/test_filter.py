"""Tests for logslice.filter."""

import pytest

from logslice.filter import FilterError, filter_entries, matches


SAMPLE_ENTRIES = [
    {"level": "info", "msg": "server started", "code": 200},
    {"level": "error", "msg": "connection refused", "code": 500},
    {"level": "info", "msg": "request handled", "code": 201},
    {"level": "warn", "msg": "slow query detected", "code": 200, "meta": {"db": "pg"}},
]


class TestMatches:
    def test_exact_match(self):
        assert matches({"level": "info"}, {"level": "info"})

    def test_exact_no_match(self):
        assert not matches({"level": "info"}, {"level": "error"})

    def test_missing_field_no_match(self):
        assert not matches({"level": "info"}, {"missing": "value"})

    def test_contains_match(self):
        assert matches({"msg": "hello world"}, {"msg__contains": "world"})

    def test_contains_no_match(self):
        assert not matches({"msg": "hello world"}, {"msg__contains": "bye"})

    def test_gte_match(self):
        assert matches({"code": 500}, {"code__gte": 400})

    def test_gte_no_match(self):
        assert not matches({"code": 200}, {"code__gte": 400})

    def test_lte_match(self):
        assert matches({"code": 200}, {"code__lte": 299})

    def test_lte_no_match(self):
        assert not matches({"code": 500}, {"code__lte": 299})

    def test_dot_notation_nested_field(self):
        entry = {"meta": {"db": "pg"}}
        assert matches(entry, {"meta.db": "pg"})

    def test_dot_notation_missing_nested(self):
        assert not matches({"meta": {}}, {"meta.db": "pg"})

    def test_multiple_conditions_all_match(self):
        entry = {"level": "info", "code": 200}
        assert matches(entry, {"level": "info", "code": 200})

    def test_multiple_conditions_partial_match(self):
        entry = {"level": "info", "code": 500}
        assert not matches(entry, {"level": "info", "code": 200})

    def test_unknown_operator_raises(self):
        with pytest.raises(FilterError, match="Unknown filter operator"):
            matches({"x": 1}, {"x__unknown": 1})


class TestFilterEntries:
    def test_filter_by_level(self):
        result = filter_entries(SAMPLE_ENTRIES, {"level": "info"})
        assert len(result) == 2
        assert all(e["level"] == "info" for e in result)

    def test_filter_by_code_gte(self):
        result = filter_entries(SAMPLE_ENTRIES, {"code__gte": 500})
        assert result == [{"level": "error", "msg": "connection refused", "code": 500}]

    def test_filter_no_match_returns_empty(self):
        result = filter_entries(SAMPLE_ENTRIES, {"level": "debug"})
        assert result == []

    def test_filter_empty_query_returns_all(self):
        result = filter_entries(SAMPLE_ENTRIES, {})
        assert result == SAMPLE_ENTRIES
