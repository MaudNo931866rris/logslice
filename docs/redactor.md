# Redactor

The `logslice.redactor` module provides field-level and pattern-based redaction
for sensitive data in structured log streams.

## Functions

### `redact_fields(entry, fields, mask="***REDACTED***")`

Replace the values of the specified fields with a mask string.

- `entry` — a parsed log entry (`dict`).
- `fields` — list of dotted field paths to redact (e.g. `["user", "auth.token"]`).
- `mask` — replacement string (default `***REDACTED***`).

Returns a new dict; the original is not mutated.

```python
from logslice.redactor import redact_fields

entry = {"user": "alice", "msg": "login"}
print(redact_fields(entry, ["user"]))
# {'user': '***REDACTED***', 'msg': 'login'}
```

### `redact_pattern(entry, field, pattern, replacement="***REDACTED***")`

Apply a regex substitution to the string value of a single field.

- `field` — dotted path to the target field.
- `pattern` — Python `re` pattern string.
- `replacement` — substitution string.

Raises `RedactionError` if the pattern is invalid.

```python
from logslice.redactor import redact_pattern

entry = {"msg": "user email is bob@example.com"}
print(redact_pattern(entry, "msg", r"[\w.+-]+@[\w-]+\.[\w.]+"))
# {'msg': 'user email is ***REDACTED***'}
```

### `redact_entries(entries, fields=None, pattern_field=None, pattern=None, replacement="***REDACTED***")`

Apply redaction to an iterable stream of log entry dicts.

```python
from logslice.redactor import redact_entries

entries = [{"user": "carol", "level": "info"}, {"user": "dave", "level": "warn"}]
for e in redact_entries(entries, fields=["user"]):
    print(e)
```

## CLI Integration

Redaction can be composed with the pipeline before export:

```python
from logslice.pipeline import run_pipeline
from logslice.redactor import redact_entries

entries = run_pipeline(sources=["app.log"], filters=[])
for entry in redact_entries(entries, fields=["password", "token"]):
    print(entry)
```
