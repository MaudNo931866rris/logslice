"""Export filtered log entries to various output formats."""

from __future__ import annotations

import csv
import io
import json
from typing import Iterable, Iterator


class ExportError(Exception):
    """Raised when an export operation fails."""


SUPPORTED_FORMATS = ("jsonl", "csv", "tsv")


def export_jsonl(entries: Iterable[dict]) -> Iterator[str]:
    """Yield each entry serialised as a JSON line."""
    for entry in entries:
        try:
            yield json.dumps(entry, ensure_ascii=False)
        except (TypeError, ValueError) as exc:
            raise ExportError(f"Failed to serialise entry to JSON: {exc}") from exc


def export_delimited(
    entries: Iterable[dict],
    fields: list[str],
    delimiter: str = ",",
) -> Iterator[str]:
    """Yield CSV/TSV rows for the given *fields*.

    The first yielded string is the header row.
    Missing fields are represented as empty strings.
    """
    if not fields:
        raise ExportError("At least one field must be specified for delimited export.")

    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=delimiter)

    writer.writerow(fields)
    yield buf.getvalue().rstrip("\r\n")

    for entry in entries:
        buf.seek(0)
        buf.truncate()
        row = [str(entry.get(f, "")) for f in fields]
        writer.writerow(row)
        yield buf.getvalue().rstrip("\r\n")


def export_entries(
    entries: Iterable[dict],
    fmt: str,
    fields: list[str] | None = None,
    delimiter: str = ",",
) -> Iterator[str]:
    """Dispatch to the appropriate exporter based on *fmt*."""
    fmt = fmt.lower()
    if fmt == "jsonl":
        yield from export_jsonl(entries)
    elif fmt in ("csv", "tsv"):
        effective_delimiter = "\t" if fmt == "tsv" else delimiter
        if not fields:
            raise ExportError(f"'fields' must be provided for {fmt.upper()} export.")
        yield from export_delimited(entries, fields, delimiter=effective_delimiter)
    else:
        raise ExportError(
            f"Unsupported export format '{fmt}'. Choose from: {', '.join(SUPPORTED_FORMATS)}."
        )
