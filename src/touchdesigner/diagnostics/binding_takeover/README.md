# Issue #8: binding takeover experiment

Related: [issue #8](https://github.com/joshuahhn/roto_control/issues/8),
[runtime BIND ownership issue #5](https://github.com/joshuahhn/roto_control/issues/5).

Scope: verification only, as requested on 2026-10-08. These files are disposable
experiments, not production features. No runtime source, Inspector, saved mapping,
canonical toe/tox, Ableton or Bitwig code is changed. No commit, push or issue reply.
The native probe ran only after the other thread completed and live project identity
was rechecked. The active Inspector project was not saved or reloaded by this probe.

## Question and provisional verdict

Can one ownership policy feed a writable driver, while Python, reference-expression
and native-BIND strategies keep target evaluation modes stable?

The fake-clock experiment demonstrates ownership separation and idle return. Native
TD 2025.33230 verifies the owned-driver seam for all nine Float/Int/Menu × strategy
combinations, with stable modes, a same-style alias, detach and reference roundtrip.
This supports further investigation of the seam; it does not select a production
architecture. Motor movement, timeout defaults, snap versus transition, production
subscription costs and safe bidirectional target editing remain unresolved.

Two observed constraints matter: direct `.val` writes replace an expression's mode,
and native BIND alias edits back-propagate into the driver. A third constraint is
portability: the native Float tox roundtrip stored `0.9900000095367432` as `0.99`.
The bit-exact Float-value expectation failed for all three strategies; it is explicitly
recorded as `all_roundtrip_values_exact: false`, not treated as a passing check.

Open `prototype.html` directly for four interactive walkthroughs. The strategy
selector is explanatory; it does not emulate TD's dependency graph. The Python
policy used by the native runner can be checked without TD:

```sh
python3 src/touchdesigner/diagnostics/binding_takeover/prototype.py
```

## Candidate ownership contract

- An upstream CHOP channel or supported parameter supplies **target units**. A
  normalized CHOP requires an explicit range conversion; do not guess units.
- Only accepted physical movement takes manual ownership. Touch alone holds back
  motor feedback but does not manufacture a value or a physical movement.
- Movement and touch release start a full inactivity interval. Held touch cancels
  the deadline. Two seconds is an experiment value, not a selected product default.
- Upstream observations continue while manual-owned; only the latest valid value
  is retained. Return uses that sample, not a queue of old samples.
- Snap return is the first experiment. Transition requires a separate returning
  state, interpolation duration, moving-source rule, renewed-touch cancellation
  and physical acceptance before selection.
- Source deletion/nonfinite data invalidates the latest sample. Upstream-owned
  controls become unavailable and hold their last effective value. Manual-owned
  controls can finish the gesture but cannot return to an invalid cached sample.
  After idle expires, the next fresh valid sample resumes upstream ownership.
- Float values clamp to finite configured bounds. Int/Menu use the existing
  integer rounding semantics; Menu values are indices with unchanged option names
  and labels. Pulse, Toggle/button actions and arbitrary nonnumeric sources are
  excluded from this experiment.
- Feedback, ACKs and software publications cannot reset the deadline. The model
  receives already validated movement; it does **not** implement MIDI echo detection.
- Context/connection generations, target identity and attachment revision fence
  input, source observation and timers. Context switch, disconnect, LEARN, detach
  or unload discards gesture/deadline/source cache. The destination value is held;
  a newly active context needs a fresh source observation before writing.
- LOCK preserves ownership of the current routing Device; selected-Track divergence
  alone does not reset it. An accepted Device routing change does. This remains an
  integration test requirement, not behavior proved by the fake model.

`Takeover` has one replaceable timer token `(epoch, revision, deadline)`, with a fake
clock. It proves stale-callback rejection but creates no native timer. A production
adapter would cancel the previous `run`/scheduler handle and still validate the
token at callback time; source updates must not allocate timers.

## Target strategy seam to verify

Data flow: source observation → per-binding ownership → quantized accepted value
→ owned writable driver → target → existing feedback pipeline.

| Strategy | Per-update write | Target relationship | Direction |
| --- | --- | --- | --- |
| Python | Driver and validated writable target/master | Existing CONSTANT/BIND chain retained | One-way policy |
| Reference expression | Driver only | Target/master evaluates the driver's value | One-way |
| Native BIND | Driver only | Target/master binds to the driver | Natively bidirectional; policy unresolved |

Initial attachment candidates are custom Float/Int/Menu parameters whose same-style
BIND chain ends in an unclaimed writable CONSTANT Par. For an alias, attach at its
resolved master, retaining alias expressions. The probe tests scalar masters plus
one alias; arbitrary deep chains, other consumers of the master, cycles, incompatible
styles and runtime rebind remain integration gates.

Reject arbitrary existing EXPRESSION/EXPORT masters and non-Par masters. Supporting
an existing expression as a source would require an explicitly selected upstream
reference and a separate attachment/restore contract, not automatic script rewriting.
CHOP references are one-way observation sources; never write back into the CHOP.

Before attachment, capture original mode, constant value, expression, bind expression,
bind-range state, target/master runtime handles, styles, Menu semantics and ownership.
Validate the entire plan before changing a mode. Attach once and record an exact
fingerprint. Check mode/reference/master identity before every dispatch, timer write
and feedback publication. An edited reference suspends the affected binding; it
does not authorize overwriting the edit. Rollback a failed attachment only while
the partial changes still belong to it.

Detach restores the captured fields only if the attachment fingerprint still matches.
An external edit must be reported and preserved. After native BIND back-propagation,
a driver mismatch is not automatically a physical event. A first implementation
should suspend and explain this unsupported edit rather than guess a takeover or
feed the value upstream. Full bidirectional editing needs its own origin and loop
contract. The probe measures native back-propagation without adopting that policy.

Export metadata must preserve original references and the attachment fingerprint,
but never a touch/manual gesture, deadline or connected MIDI session. Runtime OP
IDs cannot be serialized as durable identities; restore must resolve saved references
and validate them before attaching. Generic exports remain empty/disconnected with
no user attachments. Clear must detach before destroying the owned driver. None of
this persistence behavior is implemented by this experiment's in-memory tox check.

## Existing integration seams and future slices

The inspected checkout uses `Binding.write` and `parameter_chain` in
`code/py/roto_python/binding.py`; `Controls` rejects shared master ownership at
registration. `_assign_control` in `RotoPythonExt.py` receives validated hardware
dispatch. `onControlChange` handles target feedback; `CollectionHost.receive`
handles touch. These are integration pointers, not a request to relax the existing
writable-target guard.

1. Retain issue #5 runtime chain ownership checks. All strategies claim target,
   aliases, writable master and driver; resolve conflicts before writes/feedback.
2. Introduce ownership at the binding/controller seam, using existing ingress epochs
   and routing/session generations. Keep old mappings on Python without migration
   side effects. Software `SetValue` needs an explicit ownership rule before adoption.
3. Add selected-source observation and one cancellable deadline per binding. Use
   selected CHOP/Par callbacks, not a whole-network scan. Same-frame echo and failure
   cases need tests through the real controller seam.
4. Add transactional attachment, detach/reload/export metadata and strategy-specific
   validation. Failed attach, edited references, duplicate masters and deleted targets
   must preserve unrelated controls and parameter modes.
5. Expose Source, Owner, Sync strategy, Return timeout/state and errors in Inspector.
   Keep HW Type, native Style, mapping Mode and numeric input preference separate.
6. Measure matched source/manual/feedback/return workloads with callback counts,
   frame/cook cost, latency, bounded subscriptions/queues/timers and long-duration
   memory. Then test physical CHOP motor/LCD follow, takeover, held touch and return.

## Verification and limitations

Offline policy checks cover tracking, held touch, release idle, duplicate-release
suppression, feedback not resetting idle, renewed movement,
latest-value return, source loss/recovery, nonfinite input, integer conversion and
stale timer/input generations. Four HTML walkthroughs check the corresponding
demonstrator scenarios. The existing checkout's 230 unit tests pass. Evidence is in
`policy_verification.json` and `native_verification.json`.

Native checks passed for follow/manual/return, stable mode/reference/alias, restoration
of original fields and local-reference tox roundtrip in all nine combinations. Int/Menu
value roundtrips were exact; Float value roundtrips had the recorded precision change.
The temporary fixture was removed, all existing root OP IDs remained, the project
remained `inspector_editor_actions.17.toe` and the final root error check was empty.

`verify_native.py` creates its own root fixture, refuses to replace an existing
fixture name and removes it in `finally`. It uses no controller, MIDI process or
project save. It checks Float/Int/Menu × Python/expression/BIND; CHOP source values,
manual/return target evaluation, mode stability, one same-style alias, original-field
restore and an in-memory native tox reference roundtrip. It also probes native BIND
target-side back-propagation and direct `.val` writes to an expression parameter.

For a repeat, first wait for other live-TD work to finish, recheck active project and run through
the bridge (substitute this checkout's absolute directory if moved):

```python
import runpy
from pathlib import Path
probe = Path('/Users/huihongnin/project/roto_control/src/touchdesigner/diagnostics/binding_takeover')
policy = runpy.run_path(str(probe / 'prototype.py'))
runner = runpy.run_path(str(probe / 'verify_native.py'))
td = dict(op=op, ParMode=ParMode, baseCOMP=baseCOMP, constantCHOP=constantCHOP,
          nullCHOP=nullCHOP, app=app, project=project)
result = runner['verify'](td, str(probe / 'native_verification.json'), policy)
print(result)
```

Timing is a 1,000-update synchronous source/write/eval microbenchmark per combination,
not a frame, subscription, callback, memory, transport-latency or physical-motor result.
No strategy is selected as faster on that basis. Full failed-attachment/edited-reference
rollback, source/target deletion callbacks, production reload, actual native timers,
LEARN/LOCK/session interactions, issue #5 cases and physical acceptance remain pending.
