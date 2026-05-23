"""Tests for the logslice CLI layer."""

import gzip
import json
import os
import tempfile

import pytest

from logslice.cli import build_parser, main, _parse_filter_args


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_tmp(lines, suffix=".log"):
    f = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False)
    for line in lines:
        f.write(json.dumps(line) + "\n")
    f.flush()
    f.close()
    return f.name


# ---------------------------------------------------------------------------
# _parse_filter_args
# ---------------------------------------------------------------------------

class TestParseFilterArgs:
    def test_eq_filter(self):
        result = _parse_filter_args(["level=error"])
        assert result == [{"field": "level", "op": "eq", "value": "error"}]

    def test_contains_filter(self):
        result = _parse_filter_args(["service~=auth"])
        assert result == [{"field": "service", "op": "contains", "value": "auth"}]

    def test_multiple_filters(self):
        result = _parse_filter_args(["level=info", "msg~=started"])
        assert len(result) == 2
        assert result[0]["op"] == "eq"
        assert result[1]["op"] == "contains"

    def test_invalid_expression_exits(self):
        with pytest.raises(SystemExit):
            _parse_filter_args(["noequalssign"])


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------

class TestMain:
    def test_plain_output(self, capsys):
        path = _write_tmp([{"level": "info", "msg": "hello"}])
        try:
            rc = main(["--plain", path])
            assert rc == 0
            out = capsys.readouterr().out
            data = json.loads(out.strip())
            assert data["msg"] == "hello"
        finally:
            os.unlink(path)

    def test_filter_reduces_output(self, capsys):
        path = _write_tmp([
            {"level": "info", "msg": "keep"},
            {"level": "error", "msg": "drop"},
        ])
        try:
            rc = main(["--plain", "-f", "level=info", path])
            assert rc == 0
            lines = [l for l in capsys.readouterr().out.strip().splitlines() if l]
            assert len(lines) == 1
            assert json.loads(lines[0])["msg"] == "keep"
        finally:
            os.unlink(path)

    def test_add_source_flag(self, capsys):
        path = _write_tmp([{"msg": "hi"}])
        try:
            main(["--plain", "--add-source", path])
            out = capsys.readouterr().out.strip()
            data = json.loads(out)
            assert "_source" in data
        finally:
            os.unlink(path)

    def test_no_sources_defaults_to_stdin(self, monkeypatch):
        """Passing no positional args should not crash argument parsing."""
        p = build_parser()
        args = p.parse_args([])
        assert args.sources == []
