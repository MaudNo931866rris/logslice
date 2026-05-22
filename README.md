# logslice

Stream and filter structured JSON logs from multiple sources with a unified query syntax.

---

## Installation

```bash
pip install logslice
```

Or install from source:

```bash
git clone https://github.com/yourname/logslice.git && cd logslice && pip install .
```

---

## Usage

Stream logs from a file and filter by field values:

```bash
logslice stream app.log --where "level=error"
```

Query multiple sources at once:

```bash
logslice stream app.log worker.log --where "service=api AND status>=500"
```

Use it programmatically in Python:

```python
from logslice import LogStream

stream = LogStream(["app.log", "worker.log"])
for entry in stream.filter(level="error", service="api"):
    print(entry)
```

Pipe JSON logs directly from stdin:

```bash
kubectl logs my-pod | logslice stream - --where "level=warn"
```

---

## Features

- Unified query syntax across multiple log sources
- Real-time streaming with low memory overhead
- Supports files, stdin, and remote sources
- Outputs clean, colorized or raw JSON

---

## License

This project is licensed under the [MIT License](LICENSE).