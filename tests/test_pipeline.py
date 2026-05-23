"""Tests for logslice.pipeline."""

import json
import os
import tempfile

import pytest

from logslice.pipeline import run_pipeline
from logslice.reader import ReaderError
from logslice.parser import ParseError


def _write_tmp(entries: list) -> str:
    fd, path = tempfile.mkstemp(suffix=".log")
    with os.fdopen(fd, "w") as fh:
        for e in entries:
            fh.write(json.dumps(e) + "\n")
    return path


class TestRunPipeline:
    def test_yields_all_entries_no_filter(self):
        path = _write_tmp([{"level": "info", "msg": "ok"}, {"level": "error", "msg": "bad"}])
        results = list(run_pipeline([path]))
        assert len(results) == 2
        os.unlink(path)

    def test_filter_applied(self):
        path = _write_tmp([
            {"level": "info", "msg": "hello"},
            {"level": "error", "msg": "oops"},
        ])
        results = list(run_pipeline([path], filters=[{"field": "level", "op": "eq", "value": "error"}]))
        assert len(results) == 1
        assert results[0]["level"] == "error"
        os.unlink(path)

    def test_add_source_injects_key(self):
        path = _write_tmp([{"msg": "hi"}])
        results = list(run_pipeline([path], add_source=True))
        assert "_source" in results[0]
        assert results[0]["_source"] == path
        os.unlink(path)

    def test_skip_invalid_ignores_bad_lines(self, tmp_path):
        p = tmp_path / "mixed.log"
        p.write_text('{"ok": true}\nnot-json\n{"ok": false}\n')
        results = list(run_pipeline([str(p)], skip_invalid=True))
        assert len(results) == 2

    def test_skip_invalid_false_raises(self, tmp_path):
        p = tmp_path / "bad.log"
        p.write_text('not-json\n')
        with pytest.raises(ParseError):
            list(run_pipeline([str(p)], skip_invalid=False))

    def test_missing_source_raises(self):
        with pytest.raises(ReaderError):
            list(run_pipeline(["/no/such/file.log"]))
