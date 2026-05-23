"""Tests for logslice.sampler."""

from __future__ import annotations

import pytest

from logslice.sampler import (
    SamplerError,
    sample_deterministic,
    sample_entries,
    sample_random,
)

ENTRIES = [{"level": "info", "msg": f"event {i}", "request_id": f"req-{i}"} for i in range(200)]


class TestSampleRandom:
    def test_rate_zero_yields_nothing(self):
        result = list(sample_random(ENTRIES, rate=0.0, seed=42))
        assert result == []

    def test_rate_one_yields_all(self):
        result = list(sample_random(ENTRIES, rate=1.0))
        assert result == ENTRIES

    def test_approximate_rate(self):
        result = list(sample_random(ENTRIES, rate=0.5, seed=0))
        # With seed=0 and 200 entries we expect roughly 100 ± 30
        assert 60 <= len(result) <= 140

    def test_seed_reproducible(self):
        a = list(sample_random(ENTRIES, rate=0.3, seed=7))
        b = list(sample_random(ENTRIES, rate=0.3, seed=7))
        assert a == b

    def test_different_seeds_differ(self):
        a = list(sample_random(ENTRIES, rate=0.5, seed=1))
        b = list(sample_random(ENTRIES, rate=0.5, seed=2))
        assert a != b

    def test_invalid_rate_raises(self):
        with pytest.raises(SamplerError):
            list(sample_random(ENTRIES, rate=1.5))

    def test_negative_rate_raises(self):
        with pytest.raises(SamplerError):
            list(sample_random(ENTRIES, rate=-0.1))

    def test_empty_input(self):
        assert list(sample_random([], rate=0.5)) == []


class TestSampleDeterministic:
    def test_rate_zero_yields_nothing(self):
        result = list(sample_deterministic(ENTRIES, rate=0.0))
        assert result == []

    def test_rate_one_yields_all(self):
        result = list(sample_deterministic(ENTRIES, rate=1.0))
        assert result == ENTRIES

    def test_same_field_value_always_same_decision(self):
        entry = {"request_id": "stable-id", "msg": "hello"}
        results = [list(sample_deterministic([entry], rate=0.5)) for _ in range(5)]
        assert all(r == results[0] for r in results)

    def test_missing_field_treated_as_empty_string(self):
        entries = [{"msg": "no id"} for _ in range(50)]
        # All share the same hash → either all in or all out
        result = list(sample_deterministic(entries, rate=0.5, field="request_id"))
        assert len(result) in (0, 50)

    def test_invalid_rate_raises(self):
        with pytest.raises(SamplerError):
            list(sample_deterministic(ENTRIES, rate=2.0))


class TestSampleEntries:
    def test_delegates_to_random_by_default(self):
        result = list(sample_entries(ENTRIES, rate=1.0))
        assert result == ENTRIES

    def test_delegates_to_deterministic(self):
        result = list(sample_entries(ENTRIES, rate=1.0, deterministic=True))
        assert result == ENTRIES

    def test_deterministic_flag_uses_field(self):
        result = list(
            sample_entries(ENTRIES, rate=0.5, deterministic=True, field="request_id")
        )
        assert 0 < len(result) < len(ENTRIES)
