# Issue #11 source review and handoff

Source-only on `t3/issue-11-comp-layout-migration`, exact common base
`61d0e03fc454dba496618fdf33ab4a5169437b19`. #9's native dependency was read live
as CLOSED; #11 remains OPEN with no comments and no #10 blocker. The clean bound
worktree was fast-forwarded without stash/reset/clean or another worktree.

## Standards

Independent Standards reviewer: zero unresolved concrete documented-standard
violations after review, fixes and targeted re-reviews. One nonblocking possible
Feature Envy heuristic remains: transaction plumbing manages manager/follower/host
private state in `layout_migration.apply`. This is documented technical coupling,
not a failed acceptance gate. The API docstring now says no **target** Par writes;
controller presentation selectors are updated transactionally.

## Spec

Independent Spec reviewer reproduced one P2: unrelated inactive unavailable owner
handles caused a valid migration to KeyError after recovery creation. The fixed
loop retains unavailable records without acquiring a handle; missing, conflict
and unregistered cases compare every retained atomic Device. Source Focus/owner
metadata is flushed before plan/apply and fresh quarantine is rechecked.

Final complete review and subsequent narrow reviews: zero new concrete findings,
zero unresolved findings. Re-review covered native mode/OP-locator recovery,
explicit saved-active versus entry policy, selection baseline preservation,
fresh pending/ingress fences during rollback, and mode-only scope compatibility.

## Checks and preserved source attempts

- Final runtime suite: **312 tests PASS** (`python3 -m unittest discover -q` from
  `src/touchdesigner`, with bytecode writes disabled). Common baseline was 276;
  36 #11 test methods include subcases for all state/failure conditions.
- Inspector suite: **211 tests PASS**. No Inspector source/UI file was changed.
- `git diff --check`, cached diff check and explicit new-file whitespace checks
  PASS. New Python/native-fixture source syntax compile PASS, not native execute.
- Immutable candidate script includes new files, applies the exact patch to a
  plain temporary common-base source mirror and verifies every file SHA-256.
  This is not a second worktree, commit or native deployment.
- Initial source run had two test-fixture expectations corrected: injection now
  fails the locked commit, not the earlier flush; CUSTOM rejection uses a fresh
  migration ID rather than deliberately reusing a completed request ID. No
  runtime check was weakened. A native-like mock initially omitted OP `isOP` and
  `eval`; it was corrected to exercise portable capture and mode compensation.
- All prior immutable source candidate directories remain preserved under the
  temporary root, including `m6k2e1gw` (reviewed P2), `oiz96jnj`, `r4_wh1az`,
  `pxougnbk`, `_n4xy2ep` and `ii4p9_sp`. The final reviewed runtime patch is
  `ii4p9_sp/candidate.patch`, SHA-256
  `60f7baf7826aa06b99fba5e34a3b3e7a62ba61137dcd8520ecef475d38c05574`.
  Final packaging adds this review record; root receives its exact patch/manifest.

## #10 comparison and remaining gates

Read-only contract comparison with frozen #10 v2 `issue-10-owner-follow.md`:
authoritative unique owner lookup, saved active Track/Device plus bound qualified
Focus/live handle, no entry/name/order fallback. #11's `active_variants` explicitly
sets those existing saved IDs; `entries` is independent. Plan/receipt exposes
selection changes. It preserves observation baseline and mode-only scope, never
lowers ingress epoch, and retains fresh intent/fence across successful rollback
for next-flush validation. It neither imports #10 runtime code nor rewrites its
pending origin/generation/owner payload. Root composes separate candidates.

Native `native_migration_fixture.py` is prepared but **NOT EXECUTED**. Root and the
Inspector sole executor must coordinate source/DAT installation and geometry,
full pre/post inventory/invariants, failure/recovery injection, actual project /
managed tox save-load / rerun / upgrade, generic export-load and Pulse observer.
Physical evidence must establish previously learned source identities then recall
them after migration without re-LEARN, with explicit classification evidence and
new matching per-control ACKs. The 14-case matrix is in the implementation contract.

No shared live TD call, source install, Connect, project switch, second MIDI host,
canonical save/export, user mapping change, other worktree mutation, GitHub write,
feature commit/push or issue close occurred here. Existing source/physical #9
evidence is preserved, not reused as #11 acceptance. Root owns final delivery.

## Accepted #12 integration — 2026-10-09

Accepted dependency is local TREE `55ef1a5febecb6c4f2428e49e899e15d5c030fd8`,
not a commit. The original immutable eight-file candidate `zd8s9h46` and every
prior review/failure/recovery remain untouched. Its eight hashes matched dirty
source before applying #12's exact accepted patch by hunks. HEAD and the real
index remain on common `61d0e03`; no fake fast-forward or whole-file replacement.

The new delta is measured against accepted #12. Shared Action/publication/ACK/
owner/Inspector code is preserved; only Plan/Apply API methods and the migration
DAT embedding differ in shared files. Migration validates named Button/Pulse
references without calling providers; anonymous callbacks remain unsupported.
Four added interop regressions cover runtime results/bindings/IDs on relocation,
unavailable off-page Actions plus CUSTOM/reload, full recovery after publication
failure, and invalid descriptors without repair. One test's invalid-knob fixture
initially collided with an existing slot; the fixture now uses slot 2. No runtime
check was weakened. Runtime **356 PASS**, Inspector **223 PASS**, diff check PASS.

The clean-demo native fixture includes one saved explicit Action registration and
asserts zero automatic Recall. The contract replaces extended physical prose with
five direct Inspector-executed migration/CAS/rollback/save-load/export/physical
steps; all applicable 14-case evidence gates remain pending. No new live call or
native rehearsal occurred. #10 implementation remains separate; saved-active
variant policy and fresh-intent fences remain unchanged.

Bounded independent Standards/Spec verdicts accompany the immutable candidate.
Packaging uses one temporary index and exact tree delta, with a complete assembled
TD source archive for native __file__ resolution; no external validation framework,
additional worktree, commit, source deployment or repeated hash campaign.

## Actual native import finding and bounded source correction

Root accepted the prior exact candidate TREE `bc3566b2f60fb1c8c7c08ca2c720f3bd200d4f13`
source gate and preserved its eight-file pin `rkk63x0s`. Native run
`roto-issue11-direct-empty-zcczqy9k` passed six public RemoveControl('Value')
preparation checks and exact fixture.seed, then the first public Plan failed:
RotoPythonExt:1518 -> layout_migration.plan:299 -> build_plan:103 ->
TouchInit.tdcustomimport:47, ModuleNotFoundError: No module named 'layouts'.
`plan_failure.json` SHA256
`113fb0220e341dc76c1fec3895f4796eef5b5b2c9d974c3de88b006589a1a15d`.
Apply count zero, no plan result/effects, observer empty, Action recalls zero,
Amounts 5/5; root accepted mandatory restoration. This is a Plan finding;
the second bare import in Apply was source-audited, not an actual Apply failure.

Shortest existing-file regression executes the real helper source in a DAT-local
namespace and calls the real public Plan, with the real shared layouts module
available through the controller and only helper-local standalone layouts import
unavailable. Before the fix it reproduces the exact ModuleNotFoundError/call chain.
Original helper bytes, regression source, RED log and native failure are retained
immutable in `roto-issue11-nativeimport-diagnosis-xgrgyz2_`. Test-only isolated
__builtins__ models the native import boundary; no process import cache or sys.path
is changed, and Plan/build_plan are not mocked.

Confirmed mechanism: function-local bare Python imports cannot resolve the sibling
DAT despite its installed Layouts manager. Both dependency sites now use one
strict local DAT resolver. Missing/invalid/non-DAT/foreign/unreadable/other-class/
bad-constants cases reject Plan/Apply before recovery/commit. Shared constants and
ActivationRollbackError come from the actual installed module, not copies.
The same public Plan regression is GREEN; public Apply/idempotence/full recovery
and failed rollback use that shared exception with standalone imports unavailable.
Runtime **359 PASS**, Inspector **223 PASS**, diff/syntax PASS (source-only).
Public API/guards/CAS/recovery/mapping/Action/publication/ACK/UI code is unchanged.
Unchanged fixture.seed is not edited to mask empty preparation.

Exactly one new bounded independent Standards/Spec pair reviews prior accepted
bc3566b -> corrected source, with prior zero findings, actual native failure and
all remaining native gates supplied. Its original verdicts/task IDs accompany the
new immutable pin; any finding/byte change requires root adjudication before
another pair. No native resume is implied. Root source acceptance and separate
Inspector sole-executor resume are required for actual Plan/Apply then direct
remaining save-load/export/rollback/physical/restoration gates.
