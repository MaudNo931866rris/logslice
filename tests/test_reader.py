"""Tests for logslice.reader."""

import gzip
import os
import tempfile
import pytest

from logslice.reader import stream_file, stream_sources, ReaderError


def _write_tmp(lines: list, suffix: str = ".log") -> str:
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    return path


def _write_gz(lines: list) -> str:
    fd, path = tempfile.mkstemp(suffix=".gz")
    os.close(fd)
    with gzip.open(path, "wt") as fh:
        fh.write("\n".join(lines) + "\n")
    return path


class TestStreamFile:
    def test_reads_plain_file(self):
        path = _write_tmp(['{"a": 1}', '{"b": 2}'])
        lines = list(stream_file(path))
        assert lines == ['{"a": 1}', '{"b": 2}']
        os.unlink(path)

    def test_reads_gzip_file(self):
        path = _write_gz(['{"x": 10}'])
        lines = list(stream_file(path))
        assert lines == ['{"x": 10}']
        os.unlink(path)

    def test_missing_file_raises(self):
        with pytest.raises(ReaderError, match="File not found"):
            list(stream_file("/nonexistent/path/file.log"))

    def test_directory_raises(self, tmp_path):
        with pytest.raises(ReaderError, match="Not a regular file"):
            list(stream_file(str(tmp_path)))


class TestStreamSources:
    def test_multiple_files(self):
        p1 = _write_tmp(['{"n": 1}'])
        p2 = _write_tmp(['{"n": 2}'])
        results = list(stream_sources([p1, p2]))
        sources = [s for s, _ in results]
        assert p1 in sources and p2 in sources
        os.unlink(p1)
        os.unlink(p2)

    def test_empty_sources_reads_nothing_without_stdin(self, monkeypatch):
        import io
        monkeypatch.setattr("sys.stdin", io.StringIO(""))
        results = list(stream_sources([]))
        assert results == []
