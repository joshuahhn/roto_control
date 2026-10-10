# Issue #12: named Action presets

Implementation brief: source-only work on `t3/issue-12-action-presets`; no dependency on #9 ownership allocation or #13 Snapshot values.

- Register explicit stable action IDs/labels and consumer recall callbacks. Runtime callables are rebuilt by `registration.onRegisterActions(controller)` before saved mappings restore in either setup mode. No callable, callback return object or target value is serialized.
- Assign a registered action to one Button, keeping unrelated adapters and mappings. Persist action ID plus independent mapping ID, slot/index, Pulse mode and PUSH/TOGGLE adapter in the existing Device/Layout library.
- Dispatch only through existing acknowledged, unfenced collection input. PUSH fires on a rising edge, TOGGLE keeps the established latched-press adapter. Metadata, selection, reload and software feedback never recall.
- Return detached `succeeded`, `unavailable`, `failed` or `partial` results. Failures isolate the Button and retain the MIDI session; arbitrary consumer side effects are not rolled back. Existing parameter watchers publish actual values.
- Generic export clears mappings/runtime actions and replaces both consumer hooks. Test CUSTOM and existing COMP-linked contexts, reconstruction, page recall, guards and failure isolation without introducing ownership metadata.

Native gate: prepare a disconnected isolated fixture for coordinated execution; do not touch shared live TD/canonical binaries. Record native and physical evidence separately. No commit/push/merge authorization.

## Source delivery and remaining gates

Consumer API/result/reconstruction contract: [actions](../functions/actions.md). Source tests: [test_action_presets.py](../../test_action_presets.py); prepared native stages: [verify_action_presets.py](../../verify_action_presets.py). 24 new runtime tests plus 4 Inspector integration tests; full suites 300 runtime / 215 Inspector / OK. Native harness is syntax-checked only, not executed. Native TD reload/export and physical acceptance remain pending; #12/#13 native dependency is not satisfied.

Composed base revision `61d0e03fc454dba496618fdf33ab4a5169437b19`; changes remain unstaged/uncommitted in this thread's worktree. A complete review patch with SHA-256 is reported in the integration handoff; it includes new source/docs/tests without staging them. #13 provider may return success, validation_failed, execution_failed or partial plus JSON-safe entry/readback details; the action seam propagates those outcomes. No Snapshot implementation is included.

## Common-base composition and review

The original 251-test source handoff is preserved in a verified 13-file archive and retained scoped stash. This worktree safe fast-forwarded to accepted #9/Inspector source, then resolved four overlapping files by hunks; no old full-file replacement, feature commit or shared-TD change.

Independent r1 Standards/Spec review found missing owner/quarantine checks in explicit software recall and incomplete current Inspector action projection. Both are fixed with regression coverage for missing/conflict/unregistered/returned owners, real COMP/CUSTOM libraries, full provider details, unavailable-after-success, action freshness and Pulse-only schema. R2 re-review is required before the final candidate is handed to root.

Native request is only the new Action feature: disconnected real COMP/CUSTOM fixture, provider callback/result diagnostics, exactly-once synthetic PUSH/TOGGLE, watchers/readback feedback, registration reconstruction and actual tox/generic reload. Physical request is a single coordinated new Button action/LED/LCD/parameter-feedback batch with root's existing restoration capture; do not repeat already accepted #9 ownership/SEL/FUNC physical gates. Root/Inspector is sole executor.
