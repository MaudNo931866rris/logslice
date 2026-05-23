"""Integration tests: redactor working with pipeline and transformer."""

from logslice.redactor import redact_entries
from logslice.transformer import add_field, drop_fields
from logslice.deduplicator import deduplicate


def _stream(entries):
    yield from entries


def test_redact_after_add_field():
    """Fields added by transformer are redactable."""
    entries = [{"msg": "login", "user": "alice"}]
    enriched = [add_field(e, "env", "prod") for e in entries]
    redacted = list(redact_entries(enriched, fields=["user", "env"]))
    assert redacted[0]["user"] == "***REDACTED***"
    assert redacted[0]["env"] == "***REDACTED***"
    assert redacted[0]["msg"] == "login"


def test_redact_before_dedup():
    """Deduplication works correctly on redacted entries."""
    entries = [
        {"user": "alice", "msg": "hello"},
        {"user": "bob", "msg": "hello"},
    ]
    redacted = list(redact_entries(entries, fields=["user"]))
    # Both entries now have same user value; dedup on msg only
    deduped = list(deduplicate(_stream(redacted), fields=["msg"]))
    assert len(deduped) == 1


def test_drop_then_redact():
    """Dropped fields do not appear after redaction."""
    entries = [{"user": "alice", "secret": "tok123", "msg": "ok"}]
    dropped = [drop_fields(e, ["secret"]) for e in entries]
    redacted = list(redact_entries(dropped, fields=["user"]))
    assert "secret" not in redacted[0]
    assert redacted[0]["user"] == "***REDACTED***"


def test_pattern_redact_preserves_structure():
    """Pattern redaction on nested fields preserves surrounding structure."""
    from logslice.redactor import redact_pattern

    entry = {"auth": {"header": "Bearer eyJhbGci.payload.sig"}, "level": "debug"}
    result = redact_pattern(entry, "auth.header", r"Bearer \S+", "Bearer [TOKEN]")
    assert result["auth"]["header"] == "Bearer [TOKEN]"
    assert result["level"] == "debug"
