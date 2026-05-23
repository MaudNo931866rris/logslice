"""Tests for logslice.aggregator."""

import pytest
from collections import Counter

from logslice.aggregator import AggregationError, count_by, group_by, top_n


SAMPLE_ENTRIES = [
    {"level": "INFO",  "service": "api",   "msg": "started"},
    {"level": "ERROR", "service": "api",   "msg": "failed"},
    {"level": "INFO",  "service": "worker","msg": "processing"},
    {"level": "WARN",  "service": "api",   "msg": "slow"},
    {"level": "INFO",  "service": "worker","msg": "done"},
    {"level": "ERROR", "service": "db",    "msg": "timeout"},
]


class TestCountBy:
    def test_counts_existing_field(self):
        result = count_by(SAMPLE_ENTRIES, "level")
        assert result["INFO"] == 3
        assert result["ERROR"] == 2
        assert result["WARN"] == 1

    def test_missing_field_counted_under_none(self):
        entries = [{"level": "INFO"}, {"other": "x"}]
        result = count_by(entries, "level")
        assert result["INFO"] == 1
        assert result[None] == 1

    def test_empty_entries_returns_empty_counter(self):
        result = count_by([], "level")
        assert result == Counter()

    def test_nested_field(self):
        entries = [
            {"meta": {"env": "prod"}},
            {"meta": {"env": "dev"}},
            {"meta": {"env": "prod"}},
        ]
        result = count_by(entries, "meta.env")
        assert result["prod"] == 2
        assert result["dev"] == 1


class TestGroupBy:
    def test_groups_by_field(self):
        result = group_by(SAMPLE_ENTRIES, "service")
        assert set(result.keys()) == {"api", "worker", "db"}
        assert len(result["api"]) == 3
        assert len(result["worker"]) == 2
        assert len(result["db"]) == 1

    def test_missing_field_grouped_under_none(self):
        entries = [{"level": "INFO"}, {"other": "x"}]
        result = group_by(entries, "level")
        assert len(result["INFO"]) == 1
        assert len(result[None]) == 1

    def test_empty_entries_returns_empty_dict(self):
        assert group_by([], "level") == {}


class TestTopN:
    def test_returns_top_values(self):
        result = top_n(SAMPLE_ENTRIES, "level", n=2)
        assert result[0] == ("INFO", 3)
        assert result[1] == ("ERROR", 2)

    def test_n_larger_than_distinct_values(self):
        result = top_n(SAMPLE_ENTRIES, "level", n=100)
        assert len(result) == 3

    def test_invalid_n_raises(self):
        with pytest.raises(AggregationError):
            top_n(SAMPLE_ENTRIES, "level", n=0)

    def test_n_defaults_to_ten(self):
        entries = [{"k": str(i)} for i in range(20)]
        result = top_n(entries, "k")
        assert len(result) == 10
