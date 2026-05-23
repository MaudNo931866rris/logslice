"""Stream log entries from files, stdin, or URLs."""

import sys
import gzip
import bz2
from pathlib import Path
from typing import Iterator, Union


class ReaderError(Exception):
    """Raised when a log source cannot be read."""
    pass


def _open_file(path: str):
    """Open a file, handling compressed formats transparently."""
    p = Path(path)
    if not p.exists():
        raise ReaderError(f"File not found: {path}")
    if not p.is_file():
        raise ReaderError(f"Not a regular file: {path}")
    if p.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8")
    if p.suffix == ".bz2":
        return bz2.open(path, "rt", encoding="utf-8")
    return open(path, "r", encoding="utf-8")


def stream_file(path: str) -> Iterator[str]:
    """Yield raw lines from a log file."""
    try:
        with _open_file(path) as fh:
            for line in fh:
                yield line.rstrip("\n")
    except ReaderError:
        raise
    except OSError as exc:
        raise ReaderError(f"Cannot read {path}: {exc}") from exc


def stream_stdin() -> Iterator[str]:
    """Yield raw lines from stdin."""
    for line in sys.stdin:
        yield line.rstrip("\n")


def stream_sources(sources: list) -> Iterator[tuple]:
    """Yield (source_name, raw_line) tuples from a list of file paths.

    Pass an empty list or ['-'] to read from stdin.
    """
    if not sources or sources == ["-"]:
        for line in stream_stdin():
            yield ("<stdin>", line)
        return

    for path in sources:
        if path == "-":
            for line in stream_stdin():
                yield ("<stdin>", line)
        else:
            for line in stream_file(path):
                yield (path, line)
