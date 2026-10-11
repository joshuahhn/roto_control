# Diagnostics and JSON evidence

- `runtime/results/`: former root verification JSON/JSONL.
- `inspector/results/`: former prototypes/inspector JSON/JSONL captures.
- Other named folders retain their existing scoped evidence, scripts and artifacts.
- `organization/artifact_moves.json`: original path, new path, size and SHA256
  for every relocated artifact. Existing result payloads were not rewritten.

Saved projects to open are indexed in [projects](../projects/README.md).
New captures belong in a named diagnostics folder, not the source root or UI code.
