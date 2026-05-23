"""
logslice.ratelimiter
~~~~~~~~~~~~~~~~~~~~
Rate-limit a stream of log entries by time window, emitting at most
*max_count* entries per *window_seconds* based on a timestamp field.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Iterator

__all__ = ["RateLimiterError", "rate_limit", "rate_limit_by_key"]


class RateLimiterError(Exception):
    """Raised when rate-limiter configuration is invalid."""


def _bucket(ts: float, window: float) -> int:
    """Return the integer bucket index for a timestamp."""
    return int(ts // window)


def rate_limit(
    entries: Iterable[dict],
    max_count: int,
    window_seconds: float = 1.0,
    timestamp_field: str = "ts",
) -> Iterator[dict]:
    """Yield entries, dropping those that exceed *max_count* per window.

    Entries whose timestamp field is missing or non-numeric are always
    passed through unchanged.

    Args:
        entries: Iterable of parsed log dicts.
        max_count: Maximum entries allowed per window.
        window_seconds: Length of each time bucket in seconds.
        timestamp_field: Field name carrying a Unix timestamp (float/int).

    Raises:
        RateLimiterError: If *max_count* < 1 or *window_seconds* <= 0.
    """
    if max_count < 1:
        raise RateLimiterError("max_count must be >= 1")
    if window_seconds <= 0:
        raise RateLimiterError("window_seconds must be > 0")

    counts: dict[int, int] = defaultdict(int)

    for entry in entries:
        raw = entry.get(timestamp_field)
        if raw is None:
            yield entry
            continue
        try:
            ts = float(raw)
        except (TypeError, ValueError):
            yield entry
            continue

        bucket = _bucket(ts, window_seconds)
        if counts[bucket] < max_count:
            counts[bucket] += 1
            yield entry


def rate_limit_by_key(
    entries: Iterable[dict],
    key_field: str,
    max_count: int,
    window_seconds: float = 1.0,
    timestamp_field: str = "ts",
) -> Iterator[dict]:
    """Like :func:`rate_limit` but applies a separate budget per *key_field* value.

    Entries missing *key_field* are grouped under the sentinel ``None``.

    Raises:
        RateLimiterError: If *max_count* < 1 or *window_seconds* <= 0.
    """
    if max_count < 1:
        raise RateLimiterError("max_count must be >= 1")
    if window_seconds <= 0:
        raise RateLimiterError("window_seconds must be > 0")

    counts: dict[tuple, int] = defaultdict(int)

    for entry in entries:
        key = entry.get(key_field)
        raw = entry.get(timestamp_field)
        if raw is None:
            yield entry
            continue
        try:
            ts = float(raw)
        except (TypeError, ValueError):
            yield entry
            continue

        bucket = _bucket(ts, window_seconds)
        composite = (key, bucket)
        if counts[composite] < max_count:
            counts[composite] += 1
            yield entry
