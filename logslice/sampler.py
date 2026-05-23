"""Random and deterministic sampling of log entry streams."""

from __future__ import annotations

import hashlib
import random
from typing import Iterable, Iterator


class SamplerError(Exception):
    """Raised when sampling parameters are invalid."""


def _hash_entry(entry: dict, field: str) -> int:
    """Return a stable integer hash of *entry[field]* for deterministic sampling."""
    value = str(entry.get(field, ""))
    digest = hashlib.md5(value.encode(), usedforsecurity=False).hexdigest()
    return int(digest, 16)


def sample_random(
    entries: Iterable[dict],
    rate: float,
    seed: int | None = None,
) -> Iterator[dict]:
    """Yield each entry with probability *rate* (0.0 – 1.0).

    Args:
        entries: Iterable of parsed log entry dicts.
        rate: Fraction of entries to keep (e.g. 0.1 keeps ~10 %).
        seed: Optional RNG seed for reproducible results.

    Raises:
        SamplerError: If *rate* is not in [0.0, 1.0].
    """
    if not (0.0 <= rate <= 1.0):
        raise SamplerError(f"rate must be between 0.0 and 1.0, got {rate!r}")
    rng = random.Random(seed)
    for entry in entries:
        if rng.random() < rate:
            yield entry


def sample_deterministic(
    entries: Iterable[dict],
    rate: float,
    field: str = "request_id",
) -> Iterator[dict]:
    """Yield entries whose *field* hash falls within the *rate* bucket.

    This ensures the same logical entity (e.g. request) is always included
    or excluded, which is useful for tracing correlated log lines.

    Args:
        entries: Iterable of parsed log entry dicts.
        rate: Fraction of entries to keep (0.0 – 1.0).
        field: Field whose value drives the hash decision.

    Raises:
        SamplerError: If *rate* is not in [0.0, 1.0].
    """
    if not (0.0 <= rate <= 1.0):
        raise SamplerError(f"rate must be between 0.0 and 1.0, got {rate!r}")
    threshold = int(rate * (2**128))
    for entry in entries:
        if _hash_entry(entry, field) < threshold:
            yield entry


def sample_entries(
    entries: Iterable[dict],
    rate: float,
    *,
    deterministic: bool = False,
    field: str = "request_id",
    seed: int | None = None,
) -> Iterator[dict]:
    """Unified sampling entry point used by the pipeline."""
    if deterministic:
        return sample_deterministic(entries, rate, field=field)
    return sample_random(entries, rate, seed=seed)
