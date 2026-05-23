"""
Tests for logslice.ratelimiter.
"""

import pytest

from logslice.ratelimiter import (
    RateLimiterError,
    rate_limit,
    rate_limit_by_key,
)


def _entries(timestamps, field="ts", extra=None):
    """Build a list of minimal log dicts."""
    return [{field: t, **(extra or {})} for t in timestamps]


# ---------------------------------------------------------------------------
# rate_limit
# ---------------------------------------------------------------------------

class TestRateLimit:
    def test_all_pass_within_budget(self):
        entries = _entries([1.0, 1.1, 1.8])  # all in bucket 1 (window=1)
        result = list(rate_limit(entries, max_count=5, window_seconds=1.0))
        assert len(result) == 3

    def test_excess_entries_dropped(self):
        # bucket 0 (ts 0.x), max 2 → third entry dropped
        entries = _entries([0.1, 0.2, 0.3, 0.4])
        result = list(rate_limit(entries, max_count=2, window_seconds=1.0))
        assert len(result) == 2
        assert result[0]["ts"] == 0.1
        assert result[1]["ts"] == 0.2

    def test_separate_windows_each_get_budget(self):
        entries = _entries([0.5, 0.6, 1.5, 1.6])  # two buckets
        result = list(rate_limit(entries, max_count=1, window_seconds=1.0))
        assert len(result) == 2
        assert result[0]["ts"] == 0.5
        assert result[1]["ts"] == 1.5

    def test_missing_timestamp_passes_through(self):
        entries = [{"msg": "no ts"}, {"ts": 0.1}, {"msg": "also no ts"}]
        result = list(rate_limit(entries, max_count=1, window_seconds=1.0))
        # no-ts entries always pass; ts entry passes (first in bucket)
        assert len(result) == 3

    def test_non_numeric_timestamp_passes_through(self):
        entries = [{"ts": "not-a-number"}, {"ts": 0.0}]
        result = list(rate_limit(entries, max_count=1, window_seconds=1.0))
        assert len(result) == 2

    def test_invalid_max_count_raises(self):
        with pytest.raises(RateLimiterError, match="max_count"):
            list(rate_limit([], max_count=0))

    def test_invalid_window_raises(self):
        with pytest.raises(RateLimiterError, match="window_seconds"):
            list(rate_limit([], max_count=1, window_seconds=0))

    def test_custom_timestamp_field(self):
        entries = _entries([0.1, 0.2, 0.3], field="time")
        result = list(
            rate_limit(entries, max_count=2, window_seconds=1.0, timestamp_field="time")
        )
        assert len(result) == 2


# ---------------------------------------------------------------------------
# rate_limit_by_key
# ---------------------------------------------------------------------------

class TestRateLimitByKey:
    def test_separate_budget_per_key(self):
        entries = [
            {"ts": 0.1, "svc": "a"},
            {"ts": 0.2, "svc": "a"},  # dropped — budget for 'a' in bucket 0 = 1
            {"ts": 0.3, "svc": "b"},  # passes — fresh budget for 'b'
        ]
        result = list(
            rate_limit_by_key(entries, key_field="svc", max_count=1, window_seconds=1.0)
        )
        assert len(result) == 2
        assert result[0]["svc"] == "a"
        assert result[1]["svc"] == "b"

    def test_missing_key_grouped_together(self):
        entries = [
            {"ts": 0.1},
            {"ts": 0.2},  # no 'svc' key → same None bucket, dropped
        ]
        result = list(
            rate_limit_by_key(entries, key_field="svc", max_count=1, window_seconds=1.0)
        )
        assert len(result) == 1

    def test_invalid_config_raises(self):
        with pytest.raises(RateLimiterError):
            list(rate_limit_by_key([], key_field="k", max_count=0))
