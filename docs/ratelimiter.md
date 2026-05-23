# Rate Limiter

The `logslice.ratelimiter` module lets you cap the number of log entries
emitted per time window, preventing high-volume bursts from overwhelming
downstream consumers or output files.

## Functions

### `rate_limit(entries, max_count, window_seconds=1.0, timestamp_field="ts")`

Yield at most `max_count` entries per `window_seconds` bucket, based on a
Unix timestamp stored in `timestamp_field`.

```python
from logslice.ratelimiter import rate_limit

filtered = rate_limit(entries, max_count=100, window_seconds=60.0)
```

- Entries **missing** the timestamp field are always passed through.
- Entries with a **non-numeric** timestamp are always passed through.
- Raises `RateLimiterError` if `max_count < 1` or `window_seconds <= 0`.

### `rate_limit_by_key(entries, key_field, max_count, window_seconds=1.0, timestamp_field="ts")`

Same as `rate_limit`, but the budget is applied **independently per value**
of `key_field`. This is useful for per-service or per-host throttling.

```python
from logslice.ratelimiter import rate_limit_by_key

filtered = rate_limit_by_key(
    entries,
    key_field="service",
    max_count=10,
    window_seconds=1.0,
)
```

Entries where `key_field` is absent are grouped under the sentinel `None`
and share a single budget.

## CLI integration

Passed through `run_pipeline` via the `--rate-limit` and
`--rate-window` flags (planned).

## Errors

| Exception | Cause |
|---|---|
| `RateLimiterError` | Invalid `max_count` or `window_seconds` |
