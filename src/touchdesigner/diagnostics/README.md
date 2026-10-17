# Diagnostics and JSON evidence

- `runtime/results/`: former root verification JSON/JSONL.
- `inspector/results/`: former prototypes/inspector JSON/JSONL captures.
- Other named folders retain their existing scoped evidence, scripts and artifacts.
- `organization/artifact_moves.json`: original path, new path, size and SHA256
  for every relocated artifact. Existing result payloads were not rewritten.

Saved projects to open are indexed in [projects](../projects/README.md).
One-off probes and captures default to a system temporary directory. Add a permanent
harness/result only when it has explicit reusable regression or acceptance value;
place it in a named diagnostics folder and document its scope, prerequisites and
output location. Extend an existing test first and preserve existing evidence.
Follow [change-scoped validation](../../../AGENTS.md#change-scoped-validation);
an old capture or pending gate is not a requirement to rerun it.
