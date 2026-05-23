"""High-level summary helpers built on top of the aggregator."""

from typing import Any, Dict, Iterable, List, Optional

from logslice.aggregator import count_by, group_by, top_n


def summarise(
    entries: Iterable[Dict[str, Any]],
    group_field: str = "level",
    top_fields: Optional[List[str]] = None,
    top_n_count: int = 5,
) -> Dict[str, Any]:
    """Return a summary dict for a collection of log entries.

    Parameters
    ----------
    entries:
        Iterable of parsed log entry dicts.
    group_field:
        Primary field to group / count by (default ``"level"``).
    top_fields:
        Additional fields for which to compute top-N values.
    top_n_count:
        How many top values to return for each field in *top_fields*.

    Returns
    -------
    dict with keys:
        ``total``      – total number of entries processed
        ``by_<field>`` – counter dict for *group_field*
        ``top_<f>``    – list of (value, count) for each field in *top_fields*
    """
    all_entries: List[Dict[str, Any]] = list(entries)
    result: Dict[str, Any] = {"total": len(all_entries)}

    counts = count_by(all_entries, group_field)
    result[f"by_{group_field}"] = dict(counts)

    for field in top_fields or []:
        key = f"top_{field.replace('.', '_')}"
        result[key] = top_n(all_entries, field, n=top_n_count)

    return result


def format_summary(summary: Dict[str, Any]) -> str:
    """Render a summary dict as a human-readable string."""
    lines: List[str] = [f"Total entries : {summary['total']}"]
    for key, value in summary.items():
        if key == "total":
            continue
        lines.append(f"\n{key}:")
        if isinstance(value, dict):
            for k, v in sorted(value.items(), key=lambda x: -x[1]):
                lines.append(f"  {str(k):<20} {v}")
        elif isinstance(value, list):
            for k, v in value:
                lines.append(f"  {str(k):<20} {v}")
    return "\n".join(lines)
