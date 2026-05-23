"""Deduplication utilities for log entries."""

from __future__ import annotations

import hashlib
import json
from collections import OrderedDict
from typing import Iterable, Iterator, List, Optional


class DeduplicationError(Exception):
    """Raised when deduplication cannot be performed."""


def _entry_fingerprint(entry: dict, fields: Optional[List[str]] = None) -> str:
    """Return a stable hash string for *entry*.

    If *fields* is provided only those keys contribute to the fingerprint;
    otherwise the entire entry is hashed.
    """
    if fields:
        subset = {k: entry.get(k) for k in sorted(fields)}
        payload = subset
    else:
        payload = entry
    try:
        serialised = json.dumps(payload, sort_keys=True, default=str)
    except (TypeError, ValueError) as exc:
        raise DeduplicationError(f"Cannot serialise entry for fingerprinting: {exc}") from exc
    return hashlib.sha256(serialised.encode()).hexdigest()


def deduplicate(
    entries: Iterable[dict],
    fields: Optional[List[str]] = None,
    window: Optional[int] = None,
) -> Iterator[dict]:
    """Yield entries with duplicates removed.

    Args:
        entries: Iterable of parsed log dicts.
        fields:  If given, only these fields are compared for equality.
        window:  Maximum number of recent fingerprints to remember.
                 ``None`` means remember all (global dedup).

    Yields:
        Unique log entry dicts in original order.
    """
    if window is not None and window <= 0:
        raise DeduplicationError("window must be a positive integer or None")

    seen: "OrderedDict[str, None]" = OrderedDict()

    for entry in entries:
        fp = _entry_fingerprint(entry, fields)
        if fp in seen:
            continue
        seen[fp] = None
        if window is not None and len(seen) > window:
            seen.popitem(last=False)
        yield entry
