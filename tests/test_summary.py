"""Tests for logslice.summary."""

from logslice.summary import format_summary, summarise


SAMPLE = [
    {"level": "INFO",  "service": "api",    "msg": "ok"},
    {"level": "ERROR", "service": "api",    "msg": "fail"},
    {"level": "INFO",  "service": "worker", "msg": "ok"},
    {"level": "WARN",  "service": "api",    "msg": "slow"},
    {"level": "INFO",  "service": "worker", "msg": "done"},
]


class TestSummarise:
    def test_total_count(self):
        result = summarise(SAMPLE)
        assert result["total"] == 5

    def test_default_group_field(self):
        result = summarise(SAMPLE)
        assert "by_level" in result
        assert result["by_level"]["INFO"] == 3
        assert result["by_level"]["ERROR"] == 1

    def test_custom_group_field(self):
        result = summarise(SAMPLE, group_field="service")
        assert "by_service" in result
        assert result["by_service"]["api"] == 3
        assert result["by_service"]["worker"] == 2

    def test_top_fields(self):
        result = summarise(SAMPLE, top_fields=["service"], top_n_count=2)
        assert "top_service" in result
        top = result["top_service"]
        assert top[0][0] == "api"
        assert top[0][1] == 3

    def test_top_fields_nested_key_name(self):
        entries = [{"meta": {"env": "prod"}} for _ in range(3)]
        result = summarise(entries, top_fields=["meta.env"])
        assert "top_meta_env" in result

    def test_empty_entries(self):
        result = summarise([])
        assert result["total"] == 0
        assert result["by_level"] == {}

    def test_no_top_fields_by_default(self):
        result = summarise(SAMPLE)
        assert not any(k.startswith("top_") for k in result)


class TestFormatSummary:
    def test_contains_total(self):
        summary = summarise(SAMPLE)
        output = format_summary(summary)
        assert "Total entries" in output
        assert "5" in output

    def test_contains_group_key(self):
        summary = summarise(SAMPLE)
        output = format_summary(summary)
        assert "by_level" in output
        assert "INFO" in output

    def test_contains_top_key(self):
        summary = summarise(SAMPLE, top_fields=["service"])
        output = format_summary(summary)
        assert "top_service" in output
        assert "api" in output
