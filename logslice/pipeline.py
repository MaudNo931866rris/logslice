"""Combine reader, parser, and filter into a single processing pipeline."""

from typing import Iterator, Optional

from logslice.reader import stream_sources, ReaderError
from logslice.parser import parse_line, ParseError
from logslice.filter import filter_entries


def run_pipeline(
    sources: list,
    filters: Optional[list] = None,
    add_source: bool = False,
    skip_invalid: bool = True,
) -> Iterator[dict]:
    """Stream, parse, and filter log entries from the given sources.

    Args:
        sources: List of file paths or ['-'] for stdin.
        filters: List of filter dicts as accepted by filter_entries.
        add_source: If True, inject a '_source' key into each entry.
        skip_invalid: If True, silently skip unparseable lines.

    Yields:
        Matching parsed log entry dicts.

    Raises:
        ReaderError: If a source file cannot be opened.
        ParseError: If skip_invalid is False and a line is malformed.
    """
    filters = filters or []

    raw_stream = stream_sources(sources)

    def _parsed() -> Iterator[dict]:
        for source, line in raw_stream:
            try:
                entry = parse_line(line)
            except ParseError:
                if not skip_invalid:
                    raise
                continue
            if entry is None:
                continue
            if add_source:
                entry["_source"] = source
            yield entry

    yield from filter_entries(_parsed(), filters)
