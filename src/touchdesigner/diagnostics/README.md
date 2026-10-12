# Diagnostics and JSON evidence

- `runtime/results/`: former root verification JSON/JSONL.
- `inspector/results/`: former prototypes/inspector JSON/JSONL captures.
- Other named folders retain their existing scoped evidence, scripts and artifacts.
- `organization/artifact_moves.json`: original path, new path, size and SHA256
  for every relocated artifact. Existing result payloads were not rewritten.

Saved projects to open are indexed in [projects](../projects/README.md).
Follow [change-scoped validation](../../../AGENTS.md#change-scoped-validation).
One-off probes and outputs go in a system temporary directory by default. Retain
new harnesses/results here only for an explicit reusable regression or acceptance
need, documenting scope, prerequisites and output location. Extend an existing
fixture before adding another verifier. Existing evidence and tests stay intact;
consolidation or deletion is a separate user decision.

Historical harnesses may assume the old source-root project folder or old OP paths.
Before a relevant run, inspect its target, mutation/restore behavior and output path;
use a temporary adapted copy when necessary. A path/environment failure calls for
a corrected discriminating experiment, not a new near-duplicate permanent verifier.
