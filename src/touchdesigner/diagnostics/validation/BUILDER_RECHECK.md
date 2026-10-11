# Builder recheck before push — 2026-10-11

Candidate source: isolated `t3/issue-15-validation`, after script/test/project/JSON
relocation. Native TD2025.33230 was running the durable current project under the
original checkout's `projects/current`. All fixture work occurred outside main in
`/base_builder_recheck`; no hardware MIDI process was started for test fixtures.

Recheck found and fixed two real problems:

1. Fresh `build_network` returned with pending binding restore. Immediate caller
   assignment was reverted on the first Tick to the saved default Value mapping.
   Builder now completes Applybinding and rejects initialization failure before return.
2. Native TD `Par == Par` compares numeric values. Distinct parameters with equal
   values were treated as the same destination. `_assign_target` now compares
   owner OP identity/path plus parameter name. Existing action None parameters
   and true repeated assignment keep their behavior. Regression failed before
   the fix and passes after; actual native equal-value replacement also passes.

Initial bidirectional DAT sync also rewrote authoritative Python LF files as CRLF.
Disabled initialization-time bidirectional sync in build_network/upgrade_network/
upgrade_controls, retaining explicit source reads. Restored unintended newline-only
changes; only the adapter's intentional 9-line diff remains under code/py.
A fresh native build now checks source byte hashes before/after and passes.

Passed checks:

- Fresh build from `scripts/build_network.py`: binding ready, embedded MIDI/docs,
  correct local Inspector controller, no process/errors, source bytes preserved.
- Disconnected `scripts/upgrade_layouts.py`: stable mapping/Layout identity, no
  value writes, Snapshot capture, actual equal-value destination replacement.
- `scripts/build_inspector.py`: unchanged source rebuild is idempotent.
- Configured fixture `.tox` save/load: target references local to the loaded
  fixture, local model/controller wiring, one restored Snapshot, no process/errors.
- Generic `scripts/export_component.py` + load: empty mappings/assignments/
  Snapshots, embedded DAT sources with file/sync/load flags cleared, source
  component unchanged. Export uses the explicitly configured existing Python
  interpreter because the isolated worktree has no private `.venv`.
- Runtime442 and Inspector248 tests PASS; git diff --check PASS.
- Fixtures quiesced and removed; main source hashes, registry and live PID/connection
  unchanged. Current `.toe` remains the previous physically accepted candidate,
  not silently upgraded to these new source fixes. No full-project candidate
  reload, physical retest, commit or push is claimed.

[Raw evidence and configured/generic tox artifacts](builder_recheck/).
Initial failure/diagnosis retained in `initial_failure.json`; unit-test red output
is in the session. The runtime regression is
`tests/runtime/test_assignment.py::test_equal_valued_native_parameters_are_distinct_destinations`.
Run native functions start→upgrade→exports→finish via external
`native_builder_recheck.py`, passing its disk `__file__` and TD globals. New artifact
paths are required for a subsequent export run; never overwrite existing evidence.
