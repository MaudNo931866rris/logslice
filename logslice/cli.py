"""Command-line interface for logslice."""

import argparse
import sys
from typing import List, Optional

from logslice.formatter import format_entry
from logslice.pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logslice",
        description="Stream and filter structured JSON logs from multiple sources.",
    )
    parser.add_argument(
        "sources",
        nargs="*",
        metavar="FILE",
        help="Log files to read (use '-' or omit for stdin).",
    )
    parser.add_argument(
        "-f",
        "--filter",
        dest="filters",
        action="append",
        metavar="FIELD=VALUE",
        default=[],
        help="Filter expression, e.g. level=error or service~=auth. May be repeated.",
    )
    parser.add_argument(
        "--plain",
        action="store_true",
        default=False,
        help="Disable colour output and pretty-printing; emit raw JSON lines.",
    )
    parser.add_argument(
        "--add-source",
        action="store_true",
        default=False,
        help="Inject a _source field with the filename into each entry.",
    )
    return parser


def _parse_filter_args(raw: List[str]) -> List[dict]:
    """Convert CLI filter strings into filter dicts understood by matches()."""
    result = []
    for expr in raw:
        if "~=" in expr:
            field, value = expr.split("~=", 1)
            result.append({"field": field.strip(), "op": "contains", "value": value.strip()})
        elif "=" in expr:
            field, value = expr.split("=", 1)
            result.append({"field": field.strip(), "op": "eq", "value": value.strip()})
        else:
            raise SystemExit(f"logslice: invalid filter expression: {expr!r}")
    return result


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    sources = args.sources if args.sources else ["-"]
    filters = _parse_filter_args(args.filters)

    try:
        for entry in run_pipeline(
            sources=sources,
            filters=filters,
            add_source=args.add_source,
        ):
            if args.plain:
                import json
                print(json.dumps(entry))
            else:
                print(format_entry(entry))
    except BrokenPipeError:
        pass
    except KeyboardInterrupt:
        pass

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
