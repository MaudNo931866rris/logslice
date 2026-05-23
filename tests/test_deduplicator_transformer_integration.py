"""Integration tests combining deduplicator and transformer."""

from logslice.deduplicator import deduplicate
from logslice.transformer import add_field, drop_fields


def test_dedup_after_drop_fields():
    """Dropping a unique field before dedup should collapse entries."""
    entries = [
        {"msg": "hello", "ts": 1},
        {"msg": "hello", "ts": 2},
        {"msg": "world", "ts": 3},
    ]
    without_ts = list(drop_fields(entries, ["ts"]))
    result = list(deduplicate(without_ts))
    assert len(result) == 2
    assert result[0] == {"msg": "hello"}
    assert result[1] == {"msg": "world"}


def test_add_source_then_dedup_by_msg():
    """Adding a source tag should not prevent field-based dedup on msg."""
    entries = [
        {"msg": "ping"},
        {"msg": "ping"},
        {"msg": "pong"},
    ]
    tagged = list(add_field(entries, "source", "svc-a"))
    result = list(deduplicate(tagged, fields=["msg"]))
    assert len(result) == 2
    assert all(e["source"] == "svc-a" for e in result)


def test_pipeline_order_matters():
    """Dedup before drop should keep more entries than drop before dedup."""
    entries = [
        {"msg": "a", "ts": 1},
        {"msg": "a", "ts": 2},
    ]
    # Dedup first (full entry) — different ts means both pass
    dedup_first = list(drop_fields(deduplicate(entries), ["ts"]))
    assert len(dedup_first) == 2

    # Drop first — ts gone, entries identical, only one passes
    drop_first = list(deduplicate(drop_fields(entries, ["ts"])))
    assert len(drop_first) == 1
