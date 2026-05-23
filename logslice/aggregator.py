"""Aggregation utilities for structured log entries."""

from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Optional


class AggregationError(Exception):
    """Raised when aggregation cannot be performed."""


def _get_field(entry: Dict[str, Any], field: str) -> Optional[Any]:
    """Retrieve a (possibly nested) field value using dot notation."""
    parts = field.split(".")
    current = entry
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def count_by(entries: Iterable[Dict[str, Any]], field: str) -> Counter:
    """Count log entries grouped by the value of *field*.

    Entries where *field* is absent are counted under the key ``None``.
    """
    counter: Counter = Counter()
    for entry in entries:
        value = _get_field(entry, field)
        counter[value] += 1
    return counter


def group_by(entries: Iterable[Dict[str, Any]], field: str) -> Dict[Any, List[Dict[str, Any]]]:
    """Group log entries by the value of *field*.

    Returns a dict mapping each distinct field value to the list of entries
    that carry that value.  Entries where *field* is absent are grouped under
    the key ``None``.
    """
    groups: Dict[Any, List[Dict[str, Any]]] = defaultdict(list)
    for entry in entries:
        value = _get_field(entry, field)
        groups[value].append(entry)
    return dict(groups)


def top_n(
    entries: Iterable[Dict[str, Any]], field: str, n: int = 10
) -> List[tuple]:
    """Return the *n* most common values for *field* across all entries.

    Returns a list of ``(value, count)`` pairs in descending order.
    """
    if n <= 0:
        raise AggregationError(f"n must be a positive integer, got {n!r}")
    counter = count_by(entries, field)
    return counter.most_common(n)


def frequency(entries: Iterable[Dict[str, Any]], field: str) -> Dict[Any, float]:
    """Return the relative frequency of each value for *field*.

    Each value maps to its proportion of total entries as a float between
    0.0 and 1.0.  Returns an empty dict if *entries* is empty.
    """
    counter = count_by(entries, field)
    total = sum(counter.values())
    if total == 0:
        return {}
    return {value: count / total for value, count in counter.items()}
