"""JSON log line parser for logslice."""

import json
from typing import Any, Optional


class ParseError(Exception):
    """Raised when a log line cannot be parsed."""
    pass


def parse_line(line: str) -> Optional[dict[str, Any]]:
    """
    Parse a single log line as JSON.

    Args:
        line: A raw string log line.

    Returns:
        A dictionary representing the parsed JSON log entry,
        or None if the line is empty or whitespace-only.

    Raises:
        ParseError: If the line is non-empty but not valid JSON.
    """
    line = line.strip()
    if not line:
        return None

    try:
        data = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ParseError(f"Invalid JSON log line: {exc}") from exc

    if not isinstance(data, dict):
        raise ParseError(
            f"Expected a JSON object, got {type(data).__name__}: {line!r}"
        )

    return data


def parse_lines(lines: list[str]) -> list[dict[str, Any]]:
    """
    Parse multiple log lines, skipping empty lines and collecting errors.

    Args:
        lines: Iterable of raw log line strings.

    Returns:
        A list of successfully parsed log entry dicts.
        Lines that fail to parse are skipped (error is printed to stderr).
    """
    import sys

    results: list[dict[str, Any]] = []
    for i, line in enumerate(lines, start=1):
        try:
            entry = parse_line(line)
            if entry is not None:
                results.append(entry)
        except ParseError as exc:
            print(f"[logslice] parse error on line {i}: {exc}", file=sys.stderr)
    return results
