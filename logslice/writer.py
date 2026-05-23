"""Write exported log lines to files or stdout."""

from __future__ import annotations

import gzip
import sys
from pathlib import Path
from typing import Iterable


class WriterError(Exception):
    """Raised when output writing fails."""


def write_stdout(lines: Iterable[str]) -> int:
    """Write *lines* to stdout, one per line. Returns the number of lines written."""
    count = 0
    for line in lines:
        sys.stdout.write(line + "\n")
        count += 1
    return count


def write_file(lines: Iterable[str], path: str | Path, compress: bool = False) -> int:
    """Write *lines* to *path*, optionally gzip-compressed.

    Returns the number of lines written.
    Raises WriterError on I/O failure.
    """
    path = Path(path)
    count = 0
    try:
        if compress or path.suffix == ".gz":
            opener = gzip.open(path, "wt", encoding="utf-8")
        else:
            opener = open(path, "w", encoding="utf-8")  # noqa: WPS515
        with opener as fh:
            for line in lines:
                fh.write(line + "\n")
                count += 1
    except OSError as exc:
        raise WriterError(f"Cannot write to '{path}': {exc}") from exc
    return count


def write_output(
    lines: Iterable[str],
    path: str | Path | None = None,
    compress: bool = False,
) -> int:
    """High-level helper: write to *path* if given, otherwise to stdout."""
    if path is None:
        return write_stdout(lines)
    return write_file(lines, path, compress=compress)
