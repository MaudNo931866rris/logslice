"""Tests for logslice.parser."""

import pytest

from logslice.parser import ParseError, parse_line, parse_lines


class TestParseLine:
    def test_valid_json_object(self):
        result = parse_line('{"level": "info", "msg": "started"}')
        assert result == {"level": "info", "msg": "started"}

    def test_empty_string_returns_none(self):
        assert parse_line("") is None

    def test_whitespace_only_returns_none(self):
        assert parse_line("   \n") is None

    def test_invalid_json_raises_parse_error(self):
        with pytest.raises(ParseError, match="Invalid JSON"):
            parse_line("{not valid json}")

    def test_json_array_raises_parse_error(self):
        with pytest.raises(ParseError, match="Expected a JSON object"):
            parse_line('["a", "b"]')

    def test_json_scalar_raises_parse_error(self):
        with pytest.raises(ParseError, match="Expected a JSON object"):
            parse_line('"just a string"')

    def test_nested_fields_preserved(self):
        result = parse_line('{"a": {"b": 42}}')
        assert result == {"a": {"b": 42}}


class TestParseLines:
    def test_multiple_valid_lines(self):
        lines = ['{"x": 1}', '{"x": 2}']
        assert parse_lines(lines) == [{"x": 1}, {"x": 2}]

    def test_skips_empty_lines(self):
        lines = ['{"x": 1}', "", '{"x": 3}']
        assert parse_lines(lines) == [{"x": 1}, {"x": 3}]

    def test_skips_invalid_lines_and_continues(self, capsys):
        lines = ['{"x": 1}', 'BAD', '{"x": 3}']
        result = parse_lines(lines)
        assert result == [{"x": 1}, {"x": 3}]
        captured = capsys.readouterr()
        assert "parse error" in captured.err

    def test_empty_input(self):
        assert parse_lines([]) == []
