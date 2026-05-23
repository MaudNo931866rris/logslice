"""Field transformation utilities for log entries."""

from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional


class TransformError(Exception):
    """Raised when a transformation cannot be applied."""


def _set_nested(entry: dict, key: str, value: Any) -> None:
    """Set a (possibly dotted) key in *entry*, creating intermediate dicts."""
    parts = key.split(".")
    node = entry
    for part in parts[:-1]:
        node = node.setdefault(part, {})
    node[parts[-1]] = value


def rename_field(entries: Iterable[dict], src: str, dst: str) -> Iterator[dict]:
    """Yield copies of entries with field *src* renamed to *dst*."""
    for entry in entries:
        entry = dict(entry)
        if src in entry:
            entry[dst] = entry.pop(src)
        yield entry


def drop_fields(entries: Iterable[dict], fields: List[str]) -> Iterator[dict]:
    """Yield copies of entries with *fields* removed."""
    drop = set(fields)
    for entry in entries:
        yield {k: v for k, v in entry.items() if k not in drop}


def add_field(
    entries: Iterable[dict],
    key: str,
    value: Any,
    overwrite: bool = True,
) -> Iterator[dict]:
    """Yield copies of entries with a new constant field *key* = *value*."""
    for entry in entries:
        entry = dict(entry)
        if overwrite or key not in entry:
            _set_nested(entry, key, value)
        yield entry


def apply_field(
    entries: Iterable[dict],
    key: str,
    func: Callable[[Any], Any],
) -> Iterator[dict]:
    """Yield copies of entries with *func* applied to the value of *key*.

    Entries missing *key* are passed through unchanged.
    """
    for entry in entries:
        entry = dict(entry)
        if key in entry:
            try:
                entry[key] = func(entry[key])
            except Exception as exc:
                raise TransformError(
                    f"Failed to apply transform to field '{key}': {exc}"
                ) from exc
        yield entry
