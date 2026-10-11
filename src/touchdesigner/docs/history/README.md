# Historical development documents

These plans and reports retain their original milestone claims. Consult
[CONTEXT](../../CONTEXT.md), the latest [HANDOFF](../../HANDOFF.md) entry and
[current function contracts](../functions/) for current behavior.

- [Runtime plans and protocol probe](runtime/): former TouchDesigner root plans.
- [Inspector plans and reports](inspector/): former documents beside Inspector code.
- Inspector scripts remain in
  [prototypes/inspector](../../prototypes/inspector/). Bare script filenames
  in historical reports refer to that directory, unless a full path is given.
- Runtime probe scripts now live in [diagnostics/runtime](../../diagnostics/runtime/);
  former root captures now live in `diagnostics/runtime/results`. Bare root script
  filenames in historical reports resolve via [source_moves.json](../../diagnostics/validation/source_moves.json).

The relocation manifest is [document_moves.json](../../diagnostics/validation/document_moves.json).
It records the original and current document hashes; only link/path references
were updated. Existing captured evidence and saved toe/tox artifacts are untouched.

Historical bare evidence filenames now resolve through
[artifact_moves.json](../../diagnostics/organization/artifact_moves.json); Inspector
captures are in `diagnostics/inspector/results`. Captured payloads remain unchanged.
