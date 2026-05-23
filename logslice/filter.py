"""Query-based filtering for parsed JSON log entries."""

from typing import Any


class FilterError(Exception):
    """Raised when a filter expression is invalid."""
    pass


def _get_nested(entry: dict[str, Any], key_path: str) -> Any:
    """
    Retrieve a value from a nested dict using dot-notation.

    Example: _get_nested({"a": {"b": 1}}, "a.b") -> 1
    """
    parts = key_path.split(".")
    current: Any = entry
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def matches(entry: dict[str, Any], query: dict[str, Any]) -> bool:
    """
    Determine whether a log entry satisfies all conditions in a query.

    Query format:
        {"field": value}           — exact match (dot-notation supported)
        {"field__contains": value} — substring / membership check
        {"field__gte": value}      — greater-than-or-equal
        {"field__lte": value}      — less-than-or-equal

    Args:
        entry: Parsed log entry dict.
        query: Dict of filter conditions.

    Returns:
        True if all conditions are satisfied, False otherwise.
    """
    for raw_key, expected in query.items():
        if "__" in raw_key:
            field, operator = raw_key.rsplit("__", 1)
        else:
            field, operator = raw_key, "eq"

        actual = _get_nested(entry, field)

        if operator == "eq":
            if actual != expected:
                return False
        elif operator == "contains":
            if actual is None or expected not in actual:
                return False
        elif operator == "gte":
            if actual is None or actual < expected:
                return False
        elif operator == "lte":
            if actual is None or actual > expected:
                return False
        else:
            raise FilterError(f"Unknown filter operator: {operator!r}")

    return True


def filter_entries(
    entries: list[dict[str, Any]], query: dict[str, Any]
) -> list[dict[str, Any]]:
    """Return only entries that match all conditions in *query*."""
    return [e for e in entries if matches(e, query)]
