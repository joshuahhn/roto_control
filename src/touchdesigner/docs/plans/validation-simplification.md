# Issue #15: performance-oriented validation

Source baseline: `a035d7386813b3a94bd26f57ab3514c780c6de87` (merged #2 and #16).
PR #14 closed without merge; its proposed content is not assumed implemented.
Current status: targeted native and physical tests passed; candidate installed in
the owned Inspector project with recovery. Canonical artifacts remain unchanged.

Normal performance control should be direct. Each retained check needs a concrete
failure it prevents; validation should occur at the relevant operation boundary.

## Inventory and decisions

- **Snapshot capture/dialog freshness:** refresh native definitions once for the
  context, Sync once, then check every captured Knob against that same observation.
  The confirmed command takes a new observation. Preserve all selection, membership,
  session, owner, snapshot revision and assignment-slot tokens. No persistent cache
  or bypass of the runtime Snapshot/Action authority is introduced.
- **Clear confirmation:** preserve two clicks and the eight-second confirmation
  expiry (not a forced wait). First click preflights; confirmed Clear owns its single
  fresh preflight and post-mutation Sync. UI no longer duplicates that preflight.
  Touch, LEARN, replaced target or changed session between clicks still reject.
- **Inspector lifecycle ownership:** retain open/init/attach generation checks;
  these are not per-MIDI-event validation. No measured hot-path reason to remove them.
- **Ping/recall readiness:** retain real, current ACK and identity checks. Existing
  waiting-text presentation fix is preserved; no additional refresh bypass proposed.
- **Learn, routing/Activate and Knob/Button dispatch:** unchanged. Incorrect target
  writes, stale ACKs, duplicate Pulse execution and lost mappings are concrete
  regressions, not hypothetical security concerns. Their existing checks stay.
- **Quarantine/recovery and local failures:** unchanged. Recovery still explicitly
  activates the repaired Layout; unhealthy targets do not become global bypasses.

## Source measurements

Run `python3 diagnostics/validation/measure_commands.py` from `src/touchdesigner`.
[Raw counts](../../diagnostics/validation/command_counts.json) compare the pinned
baseline with candidate code on fake adapter boundaries: four cached contexts,
eight mapped Knobs. Counts include final post-mutation observations.

- Default Snapshot intent: 9 → 1 Sync; 36 → 4 context reads.
- Explicit eight-Knob intent: 17 → 1 Sync; 68 → 4 context reads.
- Default Save confirmation: 11 → 2 Sync; 44 → 8 context reads.
- Explicit Save confirmation: 19 → 2 Sync; 76 → 8 context reads.
- Clear confirmation click: 3 → 2 Sync; 12 → 8 context reads.
- Save/Clear each dispatch exactly once. UI steps are unchanged; no forced delay
  is added or removed. Snapshot intent now refreshes the whole context's native
  definitions, including defaults that previously lacked an explicit refresh.

These are scan counts, not frame/CPU timing or hardware latency. A full-context
native-definition refresh may cost more than a narrow refresh for a small capture
set. Native measurement must check that tradeoff before claiming faster interaction.
No before/after claim is made for unchanged Learn/Activate/recall/dispatch/recovery.

## Verification proportional to the change

Always run required runtime and Inspector source checks and diff validation.
Keep wrong-target, stale ACK, persistence and exactly-once regressions. Do not
repeat hardware acceptance for byte-identical protocol/dispatch code merely because
an unrelated source file changed; record baseline, changed paths and reused evidence.
Existing #9 [integration acceptance](../../diagnostics/issue_9/integration_acceptance.md)
is baseline context, not acceptance of this candidate.

For this delta, targeted native checks are sufficient: multi-Knob Snapshot save and
confirmed save after a native definition/owner/session change, Clear confirmation
and state change between clicks, plus the affected generic source embedding path.
Measure native command/frame cost at that time. Physical MIDI acceptance is needed
if those checks reveal changed input/ACK/feedback behavior, not a new full batch by
default. Canonical saves/exports remain a separate live-TD operation with recovery.

## Completed source checks

- Runtime: 441 tests PASS; Inspector: 248 tests PASS.
- New regressions cover stale unsynced/native-definition Snapshot edits and
  Clear exactly once plus touch/LEARN/target/session changes between clicks.
- `git diff --check` PASS; 89 actual Markdown local links resolve; 27 document
  moves verified against the relocation manifest. Existing tracked JSON/JSONL,
  toe/tox and inherited integrations have no changes.
- At this source-check phase, native and physical checks were still pending;
  results from the subsequent phases follow below.

## Targeted native result — 2026-10-10

Native synchronous command measurements on real Float/Int/Menu/BIND mappings
support the batching change: default8 median2.626→0.424ms, explicit8 3.297→0.321ms,
explicit1 0.558→0.246ms (12 alternating baseline/candidate samples). Native Save
value preservation and stale native-definition rejection pass. Clear confirms once,
rechecks touch and removes the selected registration once; Sync3→2. Configured
fixture `.tox` save/load passes source parity, local ownership and Snapshot restore.
Original demo/source/mappings preserved and fixtures cleaned, zero native errors.
See [native details and limits](../../diagnostics/validation/NATIVE_TEST.md). Earlier
source-only status above records the prior phase; no physical/whole-frame claims,
generic export acceptance or original main runtime installation are inferred.

## Targeted physical result — 2026-10-11

Actual ROTO-CONTROL Knob1 input, LEARN ACK, software motor/LCD follow, Snapshot
Save/Recall, Button8 Snapshot trigger, and Clear persistence after reconnect pass.
User confirmed physical motor/LCD outcomes; native readback and actual MIDI trace
support them. Rejected0 / errors0. Candidate installed through the disconnected
external Layout builder with original main recovery. All existing Layout IDs retained.
See [physical evidence and scope](../../diagnostics/validation/HARDWARE_TEST.md).
Single command timings are not end-to-end hardware latency or whole-frame profiling.
