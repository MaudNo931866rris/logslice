"""Format log entries for terminal output."""

import json
from typing import Optional

TRY_COLORS = True
try:
    import colorama
    colorama.init(autoreset=True)
    RESET = colorama.Style.RESET_ALL
    BOLD = colorama.Style.BRIGHT
    RED = colorama.Fore.RED
    YELLOW = colorama.Fore.YELLOW
    GREEN = colorama.Fore.GREEN
    CYAN = colorama.Fore.CYAN
except ImportError:  # pragma: no cover
    TRY_COLORS = False
    RESET = BOLD = RED = YELLOW = GREEN = CYAN = ""

LEVEL_COLORS = {
    "error": RED,
    "critical": RED,
    "warning": YELLOW,
    "warn": YELLOW,
    "info": GREEN,
    "debug": CYAN,
}


def _level_color(level: str) -> str:
    return LEVEL_COLORS.get(level.lower(), "") if level else ""


def format_entry(
    entry: dict,
    fmt: str = "pretty",
    level_field: str = "level",
    message_field: str = "message",
    timestamp_field: str = "timestamp",
) -> str:
    """Format a single log entry as a string.

    fmt options:
        'json'   – compact JSON line
        'pretty' – human-readable coloured summary
    """
    if fmt == "json":
        return json.dumps(entry, ensure_ascii=False)

    # pretty
    ts = entry.get(timestamp_field, "")
    level = entry.get(level_field, "")
    msg = entry.get(message_field, json.dumps(entry, ensure_ascii=False))

    color = _level_color(str(level)) if TRY_COLORS else ""
    level_str = f"{color}{BOLD}[{level.upper()}]{RESET}" if level else ""
    ts_str = f"{ts} " if ts else ""
    return f"{ts_str}{level_str} {msg}".strip()
