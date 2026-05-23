"""Tests for logslice.writer."""

from __future__ import annotations

import gzip
import os
import tempfile
from pathlib import Path

import pytest

from logslice.writer import WriterError, write_file, write_output, write_stdout


LINES = ["line one", "line two", "line three"]


class TestWriteFile:
    def test_writes_plain_text(self, tmp_path):
        out = tmp_path / "out.log"
        count = write_file(LINES, out)
        assert count == 3
        assert out.read_text().splitlines() == LINES

    def test_writes_gzip_by_extension(self, tmp_path):
        out = tmp_path / "out.log.gz"
        write_file(LINES, out)
        with gzip.open(out, "rt") as fh:
            result = fh.read().splitlines()
        assert result == LINES

    def test_writes_gzip_via_flag(self, tmp_path):
        out = tmp_path / "out.log"
        write_file(LINES, out, compress=True)
        with gzip.open(out, "rt") as fh:
            result = fh.read().splitlines()
        assert result == LINES

    def test_returns_line_count(self, tmp_path):
        out = tmp_path / "c.log"
        assert write_file(LINES, out) == len(LINES)

    def test_invalid_path_raises_writer_error(self):
        with pytest.raises(WriterError):
            write_file(LINES, "/nonexistent_dir/out.log")

    def test_empty_lines(self, tmp_path):
        out = tmp_path / "empty.log"
        count = write_file([], out)
        assert count == 0
        assert out.read_text() == ""


class TestWriteStdout:
    def test_returns_count(self, capsys):
        count = write_stdout(LINES)
        assert count == 3

    def test_output_contains_lines(self, capsys):
        write_stdout(["hello", "world"])
        captured = capsys.readouterr()
        assert "hello" in captured.out
        assert "world" in captured.out


class TestWriteOutput:
    def test_no_path_writes_stdout(self, capsys):
        write_output(["a", "b"])
        captured = capsys.readouterr()
        assert "a" in captured.out

    def test_with_path_writes_file(self, tmp_path):
        out = tmp_path / "result.log"
        write_output(LINES, path=out)
        assert out.read_text().splitlines() == LINES
