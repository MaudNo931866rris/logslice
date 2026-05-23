"""High-level pipeline: read → parse → filter → sample → export."""

from __future__ import annotations

from typing import Iterable, Iterator

from logslice.filter import filter_entries
from logslice.parser import ParseError, parse_line
from logslice.reader import stream_sources
from logslice.sampler import sample_entries


def _parsed(lines: Iterable[str]) -> Iterator[dict]:
    """Yield successfully parsed dicts, silently dropping unparseable lines."""
    for line in lines:
        try:
            entry = parse_line(line)
            if entry is not None:
                yield entry
        except ParseError:
            continue


def run_pipeline(
    sources: list[str],
    filters: list[dict] | None = None,
    add_source: bool = False,
    sample_rate: float | None = None,
    sample_deterministic: bool = False,
    sample_field: str = "request_id",
    sample_seed: int | None = None,
) -> Iterator[dict]:
    """Stream log entries through the full processing pipeline.

    Args:
        sources: File paths or ``["-"]`` to read from stdin.
        filters: List of filter spec dicts passed to *filter_entries*.
        add_source: When *True*, inject a ``_source`` key into every entry.
        sample_rate: If given, apply sampling at this rate (0.0 – 1.0).
        sample_deterministic: Use deterministic (hash-based) sampling.
        sample_field: Field used for deterministic sampling.
        sample_seed: RNG seed for random sampling.

    Yields:
        Filtered (and optionally sampled) log entry dicts.
    """
    lines = stream_sources(sources, add_source=add_source)
    entries: Iterable[dict] = _parsed(lines)

    if filters:
        entries = filter_entries(entries, filters)

    if sample_rate is not None:
        entries = sample_entries(
            entries,
            rate=sample_rate,
            deterministic=sample_deterministic,
            field=sample_field,
            seed=sample_seed,
        )

    yield from entries
