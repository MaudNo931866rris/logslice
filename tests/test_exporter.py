"""Tests for logslice.exporter."""

from __future__ import annotations

import json
import pytest

from logslice.exporter import (
    ExportError,
    export_delimited,
    export_entries,
    export_jsonl,
)


ENTRIES = [
    {"level": "info", "msg": "started", "pid": 1},
    {"level": "error", "msg": "failed", "pid": 2},
]


class TestExportJsonl:
    def test_yields_valid_json_lines(self):
        lines = list(export_jsonl(ENTRIES))
        assert len(lines) == 2
        assert json.loads(lines[0]) == ENTRIES[0]
        assert json.loads(lines[1]) == ENTRIES[1]

    def test_empty_input_yields_nothing(self):
        assert list(export_jsonl([])) == []

    def test_non_serialisable_raises(self):
        bad = [{"key": object()}]
        with pytest.raises(ExportError):
            list(export_jsonl(bad))


class TestExportDelimited:
    def test_header_is_first_row(self):
        rows = list(export_delimited(ENTRIES, fields=["level", "msg"]))
        assert rows[0] == "level,msg"

    def test_data_rows_match_fields(self):
        rows = list(export_delimited(ENTRIES, fields=["level", "msg"]))
        assert rows[1] == "info,started"
        assert rows[2] == "error,failed"

    def test_missing_field_is_empty_string(self):
        rows = list(export_delimited(ENTRIES, fields=["level", "missing"]))
        assert rows[1] == "info,"

    def test_tsv_delimiter(self):
        rows = list(export_delimited(ENTRIES, fields=["level", "msg"], delimiter="\t"))
        assert rows[0] == "level\tmsg"

    def test_no_fields_raises(self):
        with pytest.raises(ExportError):
            list(export_delimited(ENTRIES, fields=[]))


class TestExportEntries:
    def test_jsonl_format(self):
        rows = list(export_entries(ENTRIES, fmt="jsonl"))
        assert len(rows) == 2
        assert json.loads(rows[0])["level"] == "info"

    def test_csv_format(self):
        rows = list(export_entries(ENTRIES, fmt="csv", fields=["level", "pid"]))
        assert rows[0] == "level,pid"
        assert rows[1] == "info,1"

    def test_tsv_format(self):
        rows = list(export_entries(ENTRIES, fmt="tsv", fields=["level"]))
        assert rows[0] == "level"

    def test_csv_without_fields_raises(self):
        with pytest.raises(ExportError, match="fields"):
            list(export_entries(ENTRIES, fmt="csv"))

    def test_unknown_format_raises(self):
        with pytest.raises(ExportError, match="Unsupported"):
            list(export_entries(ENTRIES, fmt="xml"))

    def test_format_case_insensitive(self):
        rows = list(export_entries(ENTRIES, fmt="JSONL"))
        assert len(rows) == 2
