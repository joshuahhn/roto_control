# Issue #10 source review

Review uses the code-review skill's independent Standards and Spec axes. Fixed
point: accepted common base `61d0e03fc454dba496618fdf33ab4a5169437b19`. No feature
commits were authorized; the pinned patch includes tracked edits and every new
file, with a complete source mirror excluding toe/tox. Review never installs TD
sources, opens MIDI or changes other worktrees.

## Standards — v1

No AGENTS/CONTEXT/HANDOFF hard breach or actionable Fowler smell. One verification
judgement concern: the native fixture's unchanged endpoint values/Pulse counts
did not justify the result label `no_value_pulse_writes`. Fixed by returning
`target_values_unchanged` and `pulse_count_unchanged` separately, leaving actual
value-write observation pending. Fixture execution remains unclaimed.

## Spec — v1

One P1: B install failure followed by successful A rollback could create a fresh
B intent, after which unconditional `recover()` reopened input. Review's frozen
repro accepted an A ACK and CC write 5→10 before the next flush. Fixed by retaining
the fence/pending intent and clearing restored controls instead of recovering.
The added regression checks ACK/CC/Pulse rejection, subsequent B commit and fresh
matching recall. No other independent Spec finding or scope creep reported.

## Re-review / evidence

The corrected candidate is frozen separately as v2. At freeze, re-review results
are a companion delivery report rather than a post-review mutation of these
source bytes. Both versions, manifests and review results are preserved. Root
receives the final exact pin and is responsible for acceptance and delivery.

v1 frozen mirror: 297 runtime / 211 Inspector PASS. Corrected focused suite:
22 PASS; final full suite is recorded in the v2 manifest. Native fixture compile
is source validation only. Native/physical #10 gates remain pending in the
[coordinated checklist](README.md).
