"""Field redaction and masking for sensitive log data."""

from __future__ import annotations

import re
from typing import Any, Iterable, Iterator


class RedactionError(Exception):
    """Raised when redaction cannot be applied."""


_MASK = "***REDACTED***"


def _set_nested(entry: dict, key_path: str, value: Any) -> dict:
    """Set a value at a dotted key path, returning a shallow-copied dict."""
    keys = key_path.split(".")
    result = dict(entry)
    node = result
    for key in keys[:-1]:
        if key not in node or not isinstance(node[key], dict):
            return result
        node[key] = dict(node[key])
        node = node[key]
    if keys[-1] in node:
        node[keys[-1]] = value
    return result


def _get_nested(entry: dict, key_path: str) -> Any:
    """Retrieve a value at a dotted key path."""
    keys = key_path.split(".")
    node: Any = entry
    for key in keys:
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    return node


def redact_fields(entry: dict, fields: list[str], mask: str = _MASK) -> dict:
    """Replace the values of *fields* with *mask*.

    Unknown or missing fields are silently ignored.
    """
    result = dict(entry)
    for field in fields:
        if _get_nested(result, field) is not None:
            result = _set_nested(result, field, mask)
    return result


def redact_pattern(
    entry: dict, field: str, pattern: str, replacement: str = _MASK
) -> dict:
    """Replace regex *pattern* matches within *field* value with *replacement*.

    Only string field values are processed; others pass through unchanged.
    """
    value = _get_nested(entry, field)
    if not isinstance(value, str):
        return entry
    try:
        new_value = re.sub(pattern, replacement, value)
    except re.error as exc:
        raise RedactionError(f"Invalid pattern {pattern!r}: {exc}") from exc
    return _set_nested(entry, field, new_value)


def redact_entries(
    entries: Iterable[dict],
    fields: list[str] | None = None,
    pattern_field: str | None = None,
    pattern: str | None = None,
    replacement: str = _MASK,
) -> Iterator[dict]:
    """Apply redaction to a stream of log entries.

    *fields*        — list of field paths to fully mask.
    *pattern_field* — field to apply regex substitution on.
    *pattern*       — regex pattern for substitution (requires *pattern_field*).
    """
    for entry in entries:
        if fields:
            entry = redact_fields(entry, fields, mask=replacement)
        if pattern_field and pattern:
            entry = redact_pattern(entry, pattern_field, pattern, replacement)
        yield entry
