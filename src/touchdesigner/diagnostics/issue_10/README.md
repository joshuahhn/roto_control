# Issue #10 coordinated acceptance and source attempts

This worktree contains source and prepared fixtures only. The shared live project,
MIDI owner, canonical artifacts and user records were not modified. Native and
physical verification belongs to root's coordinated Inspector sole executor.
No Connect, second MIDI host or project switch was performed by this thread.

## Current native/physical handoff — short direct tests

Root's Inspector sole executor uses the existing clean `demo_A`, `demo_B` and
CUSTOM contexts. Pin the composed candidate's exact TREE/diff first. This thread
has performed source tests only; no native or physical PASS is claimed.

1. With Follow on and real current NETWORKEDITOR COMP selection, select demo_A → demo_B
   → demo_A. Check committed Layout/Track/Device, LIVE Inspector and controller
   selectors; BROWSE must keep its own context. Observe each owner's live value,
   fresh real ACK and current motor/LCD/input. An idle selection must not install
   repeatedly. No Action/Preset callback or Pulse fires from selection or ACK.
2. Choose an existing qualified Device variant explicitly, leave its owner and
   return by Follow. It must return to the saved variant. Manually activate CUSTOM
   while the pane selection is unchanged: it stays CUSTOM until a new COMP
   selection. CUSTOM references never become an automatic Follow destination.
3. Select the other owner while LOCK is on: current routing/input stays active.
   Unlock with LEARN active: transition/input remains fenced until
   LEARN ends. Touch alone no longer delays automatic TD Follow. After the commit, old target input/ACK must not dispatch; current input
   resumes only on fresh matching real ACK. Check an assigned Action Button is
   silent during the transition and recalls once only on an intentional press.
4. Confirm normal LIVE/BROWSE/Activate freshness after these commits, then restore
   captured Follow/LOCK/LEARN, selection, values and controller connection state.
   Retain failed attempts and recovery as well as passing observations.

Do not repeat accepted #9 owner registration/copy/export/manual activation gates,
accepted #12 Action tests, or removed pixelSort/fractal fixtures. No external
validation framework, rehearsal campaign or second project/MIDI host is requested.
If a required saved variant or Action assignment is unavailable, report that
specific condition to root before changing mappings.

`native_follow_fixture.py` is preserved **historical, unexecuted v2 preparation**;
it is not the current test plan. The old extended checklist and complete v2
source/reviews remain in the immutable v2 bundle
`/var/folders/5q/krg7wb4d4lsgpmlmgqvywj_w0000gn/T/roto-issue10-candidate-v2-ntfh0l1w`.

Existing ROTO CC has no Layout/session token; delayed old CC after new ACK and
reused legacy hashes remain protocol limits. Source/mock evidence cannot close
physical gates. Accepted #9 manual A/B/A is not automatic #10 Follow.

## Source attempt history

- After the first runtime patch, all existing 276 runtime tests passed.
- Initial 16 new Follow tests: two failures. Variant setup called SetPluginComp,
  which intentionally invalidates the pane baseline; the tests then expected a
  first observation to activate/reject. Explicitly observed the current selection
  after linking, before introducing the new selection. No runtime guard weakened.
- Corrected 16 tests plus four lifecycle/source-order cases: 20 passed. Added an
  actual Inspector ControllerCatalog/TDControllerAdapter projection/token test:
  21 focused tests passed. Native definition inspection stays a separate gate.
- Complete suites before that final extra test: 296 runtime / 211 Inspector PASS.
  Final suite counts, review findings/fixes and candidate manifests accompany the
  immutable handoff. Native fixture compilation is source validation only.
- A whitespace wrapper initially treated no-index exit 1 as failure even though
  stdout/stderr were empty (the new file differs from /dev/null). Corrected only
  exit interpretation: accept 0/1 with zero diagnostics; every whitespace
  diagnostic still fails. The actual checks were not weakened.
- Independent v1 review confirmed one Spec P1: a fresh intent created during a
  successful rollback could lose its fence in the exception recovery path.
  Exception recovery now clears restored bindings but retains the pending gate;
  a new regression rejects old ACK/CC/Pulse before the subsequent flush, then
  requires fresh recall. Focused tests: 22 PASS. Standards' evidence-label concern
  was also fixed as described above. v1 pin and reviewer repro remain preserved.

## Accepted #12 composition

The accepted dependency is Git TREE `55ef1a5febecb6c4f2428e49e899e15d5c030fd8`,
not a commit, based on common `61d0e03fc454dba496618fdf33ab4a5169437b19`.
Its exact 20-file patch SHA256 is
`d550d2f3b563b6f3a1fa3ab0487de7269d8ca8e4647b902dc4e6457969d25c59`.
No feature commit/push/merge was fabricated. All 20 files had no textual overlap
with #10; exact patch hunks were checked then applied in this bound worktree.
Own 11 dirty files were archived and hash-verified before and after composition.
Archive: `/var/folders/5q/krg7wb4d4lsgpmlmgqvywj_w0000gn/T/roto-issue10-pre-12-integration-jako8p5u`.

The first composed suites passed 338 runtime / 223 Inspector. Six added focused
interoperability tests passed on their first run: independent Action libraries,
no selection/ACK recall, LOCK/LEARN/touch and fresh ACK, fresh commit/rollback
intents, Action-callback selection arbitration, partial-result Browse metadata,
and saved qualified variant reload. Final full-suite counts and bounded review
are pinned with the new candidate. All accepted #12 source bytes are retained.

## Follow COMP button addition after accepted v3

User explicitly requested an Inspector button to enable automatic COMP routing.
The new top-row `Follow COMP: ON/OFF` control is distinct from the `LIVE/BROWSE`
badge. Both main/popup views share `build_activation.py`; title is narrower,
button occupies the existing 88×24 header gap before the badge, with no panel,
scroll or editor height change. Native label fit is pending the new UI gate.
Hover shows actual Follow status/error or the reason the control is unavailable.

Command token covers model generation, controller session/binding, routing/owner
stamp and observed preference. Adapter freshly verifies actual local controller,
Follow parameter writable constant mode, Parameter mapping, restore/dispatch/
mutation/paused guards and active owner availability/quarantine. It writes only
`Followcomp.val`; the existing native parameter callback observes/flushes once.
It never invokes follower internals or Activate, connects MIDI, or repairs owners.
LOCK/LEARN/pending are deliberately handled by the existing callback/arbiter;
automatic Follow touch deferral is superseded by the v5 policy below,
not blocked as if this were manual Activate. Disconnected Follow is supported.

Normal Followcomp observer -> RequestSync -> shared status notification reaches
both views even with no targets or a retained BROWSE context. A preference click
does not reset local context/filter/draft. LIVE click never changes Followcomp.
A legitimate routing commit still expires stale target drafts normally.

Root accepted the unchanged v3 backend's 11 bounded native checks/restoration22
in `/var/folders/5q/krg7wb4d4lsgpmlmgqvywj_w0000gn/T/roto-issue10-direct-4ozf18o3`:
actual NETWORKEDITOR A/B/A saved AVAR (not entry), CUSTOM/idle/LIVE-BROWSE,
ActionReset0. LOCK/LEARN/touch/stale ACK were SYNTHETIC ONLY; no physical PASS.
Keep that evidence and v3 pins unchanged. New sole-executor native gate is only
the reviewed UI installation, actual OFF/ON click/native callback, both views'
state/error/availability and compact label placement, followed by root's one
human physical Follow batch and mandatory fresh restoration. No backend replay,
external validation campaign, second project/MIDI host or feature delivery here.

## V5 current gate and retained history

The explicit user policy removes touch-release wait from automatic TD COMP Follow
only. Hardware-origin selection and manual/editing/enrollment touch guards remain.
Only routing flush/diagnostic reason, Layouts selection preflight/install/rollback
and the transaction-scoped BindControls touch check change. No new preference,
UI geometry, Action/Definition guard change or unaccepted Snapshot integration.

RED evidence (actual source arbiter, mock TD boundaries):
`/var/folders/5q/krg7wb4d4lsgpmlmgqvywj_w0000gn/T/roto-issue10-v5-policy-red-4eemt7c_`.
Exact v4 fails five new policy assertions before runtime fixes; manual guard PASS.
Initial fixture used a 13-byte hardware label and failed the preserved 12-byte
check; label corrected, protocol validation unchanged. First routing-only fix
exposed BindControls touched install/rollback rejection, then transaction-scoped
permission added. A later fixture expected host touch to survive a rejected ACK's
normal host aggregation; manager touch is the authoritative retained assertion.
A direct SetValue test wrongly assumed a baseline touch guard that belongs to
Inspector Value editing; replaced with actual ConfigureControl guard coverage,
without altering SetValue or editing code. All failed attempts remain tool/history
and the initial/RED source archive; no old native failure is relabelled PASS.

Root accepted v4 UI13 plus physical A/B/A/LOCK/LEARN/current fresh ACK/selection0
scopes. Human held-A observation is retained, cause UNKNOWN; it is not diagnosed
as a source bug. Old SYNTH touch-deferral results are history for the previous
policy. #10 is still OPEN. Native/physical activity is held for the reviewed v5
pin; root's sole Inspector executor will do only minimal direct changed-policy
native and final usable-input checks, plus fresh restoration. No further human
Touch gate, accepted A/B/A replay, second host/project or new validation framework.
