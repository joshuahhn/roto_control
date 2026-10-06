# Live Select COMP build plan

Status: implemented with automated/native software verification; physical Follow acceptance pending. See comp_follow_native_verification.json and HANDOFF.md. The original planning snapshot below is historical.

Revision: incorporates the six findings in `roto-control-live-select-comp-handoff-20261007-045345.md`. The policies below define the implementation contract; acceptance evidence is recorded separately.

Follow-up revision: adds input/feedback fencing at deferred selection boundaries (P1) and transport-session lifetime for pending intents (P2). The original six contracts remain in effect.

## Scope

Primary workflow: selecting a COMP in TD selects its linked, saved Track inside the Active Layout, then existing hardware mapping recall restores the controls. Hardware-to-TD selection is a later opt-in experiment. Layout/Plugin name synchronization follows after this workflow is verified.

Keep the two existing Binding workflows. Follow operates on parameter Layouts; Python registration has no serialized Track context and reports follow unavailable. Keep the external MIDI backend and existing protocol identities.

## Live scout — 2026-10-07

This is the original planning-pass snapshot, not a fresh live verification during this revision. Re-scout the active project, geometry and errors before implementation.

- Active project: `roto_control_python.51.toe`, TD 2025.33230.
- Project root: `/roto_control_python`; controller: `/roto_control_python/roto_python`; parent shortcut: `RotoPython`.
- Outer pages: Connection, Binding, Layout. Layout currently has 11 fields.
- Controller graph: 26 immediate nodes including annotations, zero physical connections, no cycles. Control logic uses DAT modules/callbacks; existing CHOP endpoint is `base_targets/null_controls` → `out_controls`.
- Existing cleanup verification passes: four networks, 17 groups, 63 classified operators; containment, no overlaps or backward wires. Scoped operator errors are empty.
- Root functional nodes: maximum nodeX 1120, maximum right edge 1250; Y bounds -790..90. Rightmost annotation ends at X=1275.
- Layout `T` has Tracks `T` and `TRACK`, both with parameter destinations in `pixelSortV3`. They cannot be distinguished from COMP selection alone. Other empty Tracks remain available.
- `lifecycle_callbacks` already calls `parent.RotoPython.Tick()`; reuse that lifecycle, rather than adding another Execute DAT.

The project-information tool did not return a `rootPath`; the pane owner and the inspected controller's actual parent established these paths. Do not assume `/project1`.

## Selection and link rules

1. Each Track may optionally designate one Focus COMP. This is selection metadata, independent of the parameter destinations in its mappings. Cross-COMP mappings remain valid.
2. Within one Layout, a COMP can have only one automatic Follow link. Multiple manual Tracks may still control that COMP. Reject duplicate Follow links; do not choose the first matching Track.
3. Tracks without a Focus field migrate with no link. Repeated upgrades preserve existing links and Follow settings. Do not infer links from current targets, names or library order. In particular, do not automatically choose between `T` and `TRACK` for `pixelSortV3`.
4. Follow is scoped to the Active Layout. It does not search other Layouts or create Tracks/mappings. A missing, deleted or unlinked COMP leaves current routing unchanged and reports the reason.
5. Observe only `ui.panes.current` when it is an open Network Editor. The candidate is the sole member of the complete `pane.owner.selectedChildren` list, provided it is a valid, eligible COMP. Count all selected operators before filtering: COMP+TOP and two-COMP selections are both invalid. Zero selected children means no candidate even if `currentChild` remains a COMP. A sole selected COMP is the candidate even when `currentChild` differs; currentChild is diagnostic context, never a fallback or tie-breaker. Ignore controller internals and utility/system networks. Do not scan inactive panes or project-wide selected flags.
6. Only an eligible selection-set change in an already observed Network Editor, explicit Follow off→on, or `SelectComp` initiates routing. Startup, context/mode restore and entering a different pane establish a baseline without activation. A later manual Track choice is not immediately undone because the same COMP remains selected.
7. Observe pane/selection identity at approximately 10 Hz from the existing Tick. Cache link lookups; do not rediscover custom parameters or repeatedly send MIDI. There is no selection watcher DAT assumed by this plan. TD must remain playing for Tick, as in the existing MIDI workflow.
8. Sample the complete raw selection signature before returning for an invalid candidate. An observed zero/multiple/non-COMP/unlinked selection cancels an outstanding TD intent. A background click does not generate an intent from currentChild; if TD retains an identical selected set, there is no new observable event. Native tests must record that actual selected/current behavior instead of assuming the two APIs coincide.

### Pane and startup policy

- Changing current pane, closing it, changing its type, or losing a valid owner cancels a TD-origin pending intent and discards its selection baseline. If the arbiter's latest intent is hardware-origin, it remains eligible. Re-read pane identity/type/owner and the complete selected set immediately before a TD commit, even when the 10 Hz sample is not due. Ingest any newly observed change once before choosing the winner; never activate from an obsolete selection signature.
- Returning to a Network Editor, or switching between Network Editor panes/owners, records a fresh baseline and waits for a subsequent selection-set change. Do not resume the old TD request. With no usable pane, Follow reports `waiting_for_editor` and never guesses a target.
- Save the user's Follow=True preference, but reopen/reinit restores the saved routing context and enters `waiting_for_selection`. The first valid sample establishes a baseline only; it neither selects nor opens MIDI. Explicit off→on evaluates the current valid selection immediately. Selecting a different COMP or calling SelectComp is the alternative to re-enabling.
- Entering Python registration clears pending/baseline and reports follow unavailable while retaining the preference. Returning to parameter mode follows the same baseline-only policy. Disabling Follow clears runtime TD intent; it does not disable existing hardware Track selection.

## Guards and routing

Automatic Follow and deferred hardware selection use a single intent arbiter. Each observed request has a monotonic ingress sequence, source, Layout/Track IDs, connection generation and the relevant link/pane generation. Keep only the latest valid intent while LOCK, LEARN or touched controls prevent switching. Revalidate its destination, generations and all guards before applying it. An invalidated/failed latest intent is cleared; do not replay an older overwritten request as fallback. Never unmap or register new targets to follow selection.

Use existing `SelectTrack(layout_id, track_id)` activation, page-library retention, matching per-control acknowledgements and rollback. Selection alone is not proof that controls recalled. Read current target values; do not apply saved numeric presets or trigger Pulse actions.

A newer explicit hardware/manual Track selection supersedes older TD intent; a later TD selection can supersede it in turn. Existing hardware-selected Track remains distinguishable from routing Track while locked. Deleting a referenced Track/Layout, changing Active Layout, unlinking/editing its link, or reloading the extension invalidates its pending request and lookup cache. Scope/Binding-mode changes and reinit clear all pending intents; Follow off clears only TD intent.

### One activation decision per arbitration pass

Refactor the immediate unlock activation in `Layouts.receive()` into guard-state update plus intent notification. Hardware Track messages update selection/intent but do not independently activate inside the MIDI receive loop. After ingesting the current MIDI batch and sampling eligible TD selection changes, the arbiter makes at most one activation decision through the existing transactional selection path. Unlock is not itself a new selection intent, and no callback may commit recursively. A new intent arriving during commit is held for a later pass.

Observed ordering is explicit: a due TD selection sample is ingested before MIDI dispatch so it can fence the incoming batch; MIDI messages are then ingested FIFO. Immediately before commit, a TD-origin intent forces a fresh sample; a newly observed change receives the next sequence number. Commit is then considered. If the bounded receive loop leaves complete messages already buffered, defer commit until that backlog is consumed. Cross-source physical timestamps are unavailable, so this defines latest *observed* intent, not an unprovable wall-clock ordering. Samples cannot recover COMP selections changed and reversed entirely between polls.

Deferring commit does **not** permit the intervening messages to dispatch through the old host. The receive loop must apply the transition fence below at the selection/unlock message itself, before processing the next message; batching only delays activation, not input isolation.

Required examples: LOCK: TD→B, hardware→C, TD→D, unlock activates D once; reverse ordering with hardware→C last activates C once. If LEARN/touch remains active at unlock, neither case activates until every guard clears. Invalidating the winner does not first activate an older losing Track. With Follow off, deferred hardware selection still has exactly one unlock decision. Direct successful manual selection consumes/supersedes earlier intent, and is not repeated by the observer.

Direct `SelectComp(comp)` remains immediate: existing guards raise errors rather than silently queueing. Its selection uses the same validation/transaction machinery; only accepted intent supersedes older requests. Pending runtime requests are not persisted or replayed on startup.

### Selection-boundary input and feedback fence

Maintain a runtime routing epoch and a transition gate shared by Layout selection, the host/learner dispatch paths, deferred target work and outgoing feedback. It is not a new stored hardware mapping or a persisted connected state.

| Boundary | Gate policy |
| --- | --- |
| Hardware selects a different Track while unlocked | Close the gate and advance routing epoch synchronously when the valid selection message is recognized, before any following CC/mapping message reaches the old host. This applies even when activation is deferred by touch/LEARN/backlog or later fails preflight. A recognized but unavailable destination is not permission to continue routing old-target input. |
| Hardware/TD selection while LOCK retains authoritative old routing | Keep ordinary locked-context control working while LOCK stays on. Queue the intent without treating browsing as a routing change. |
| LOCK→unlocked with unresolved selection intent | Close/advance the gate inside unlock handling before returning to the receive loop, even if LEARN/touch still delays commit. There is no interval in which new unlocked input is dispatched to the formerly locked Track. |
| Accepted TD/manual selection about to change context | Close/advance the gate before activation, selection announcements or any deferred continuation. Do not close it merely for an unchanged, already-authoritative Track. If an earlier hardware boundary already fenced the context, choosing the original Track does not remove that fence. |

While the transition gate is closed:

- Consume but do not queue/replay knob CC pairs, Toggle/Cycle/Pulse/PUSH business events or context-dependent mapping reports. Do not invoke parameter writes, callbacks, FreeLearner assignment commits, page-target restoration, mapping acknowledgement or target-ready updates. This requires a control-plane-only receive path; forwarding the full message to the current host and relying on final-state checks is insufficient.
- Invalidate effective input-ready/mapped acknowledgement at gate entry while preserving registrations and stable identities. State/GetControlState must not advertise a fenced control as mapped/ready merely because the previous epoch was acknowledged. Locked browsing without a routing fence keeps the authoritative locked control ready.
- Continue parsing session/handshake/mode state, LOCK, LEARN on/off, touch on/release and transport errors, plus diagnostics. Touch release updates guards without triggering deferred value/motor feedback. Button release may update a neutral input baseline but cannot dispatch an action or feedback. Guard-clearing packets must work while every business path is fenced.
- Clear old knob-pair halves, button edge/debounce state, echo expectations and controller-owned pending target work on entry. Deferred work must carry connection generation and routing epoch and verify them before dispatch. An input half or button state from before/inside the fence cannot combine with input after it. An action already dispatched before the boundary is not retroactively undone; arbitrary user callbacks outside controller-owned queues are not claimed to be cancellable.
- Suppress target-dependent metadata, motor/LCD/LED feedback, including feedback caused by software parameter edits, touch release, timers or flush_display. Software edits may still update local TD target values; only feedback to the uncertain hardware context is fenced. Keep context-independent handshake/guard traffic available.
- Tag whole outgoing frames and decoded/deferred work with their generations; discard wholly unsent old-context frames. Preserve pipe framing for any frame already partially written, and never pretend previously transmitted bytes or commands accepted by the child can be retracted. Finish any required framing before new-context announcements; do not enqueue additional stale feedback. Retain/parse a partial inbound line for framing, but do not dispatch its business payload after an epoch change if it began in the old epoch.

The fence remains closed across Tick boundaries and receive backlog; draining a batch, clearing LOCK alone, or canceling an intent does not reopen it. After the backlog is consumed and all guards permit, commit the single winner, then issue its context/recall announcement. Move from transition-fenced to awaiting-current-context-recall: only then may new matching mapping reports establish readiness, and business input/feedback opens independently for each acknowledged control. Reports dropped during the fence are never reused as evidence. Rebuild feedback from the winner's current values; never flush an old feedback snapshot.

If selection is canceled, returns to the original Track, fails preflight or rolls back, retain the original TD routing but do **not** simply resume its old acknowledgement/input state. Once guards/backlog permit, resynchronize that retained context once and require fresh matching control recall before resuming. This is restoration of the retained context, not replay of an overwritten losing intent. A rollback failure keeps affected input fenced and pauses activation until explicit repair. An intentional session end clears session-bound gate/acknowledgement state under the next section; it never makes old controls ready.

Required trace: mapped A receives `select B → CC12 → CC44` in one batch. The gate closes at select B, both CC messages are discarded without writing A or B, and no old mapping/feedback becomes ready while B waits. Only post-commit matching B recall permits subsequent B input. The same guarantee applies when CC halves, Pulse/button messages or unlock straddle backlog/Tick boundaries. This newly introduced deferred-activation window must be closed; it is distinct from the remaining ambiguity of genuinely delayed, untagged packets arriving after a context has been re-established.

### Connection generation and disconnected Follow

Own a monotonic runtime `connection_generation` at the controller/transport boundary, independent of Layout manager lifetime and temporary host flags used during activation. Begin Connect with a new generation before opening a child, and end the generation synchronously on explicit Disconnect, failed Connect, child/pipe failure or controller teardown. Repeated Disconnect may advance/invalidate again safely. A domain activation failure with the same live child/session does not end the generation.

- Stamp every hardware intent with the generation of the owned child that supplied it. Hardware intent is eligible only in that live generation with the required session/PLUGIN readiness. Commit and any continuation verify the stamp; handshake or LOCK reset never bless an older request.
- Every session end clears **both hardware and TD pending intents**, selected/routing divergence due to old hardware browsing, receive/feedback/pairing/deferred work and session-derived LOCK/LEARN/touch/readiness. Reset hardware-selected Track to the retained routing Track. Persisted mappings, Focus links, Follow preference and the already committed TD context remain. Do not require destruction/recreation of the Layout manager to invalidate these fields. Session cleanup does not clear a domain repair-required pause from rollback failure; that still requires explicit repair/Applybinding.
- TD intents also carry the current generation, including an offline generation. On Disconnect cancel them rather than replaying/revalidating old pending requests; reset the selection baseline. Follow stays enabled as a preference and resumes baseline-only observation offline. A subsequent selection change, explicit off→on or SelectComp can create a **new** offline intent and change the local saved context without opening MIDI, issuing hardware TX or requiring stale hardware guards to clear.
- Connect cancels any still-pending offline intent, advances generation and records a fresh baseline. A context successfully committed offline is the desired context for the new handshake/recall. Newly observed TD requests during that connection attempt have its new generation and wait for required transport readiness; failed opening cancels them. Old session/child callbacks or buffers cannot activate a Track after reconnect.
- With a retained Follow=True setting, end/start of a connection never activates a previously selected COMP just because guards were cleared. Generation transitions alone produce no routing intent. Preserve disconnected selection observation in Tick despite its existing no-process early return.
- Gate/acknowledgement state and intent generations are runtime-only. Reconnect starts unmapped and admits only current-session matching recall. Already-sent untagged hardware packets can still have the documented protocol ambiguity; a host-owned stale intent, deferred callback or partial receive buffer cannot be excused as that ambiguity.

### Activation failure boundary

Keep Follow activation outside Tick's broad MIDI/transport exception handler, which currently disconnects for ValueError/RuntimeError. Introduce distinguishable domain/activation outcomes instead of classifying every ValueError or RuntimeError as transport failure.

| Failure class | Required handling |
| --- | --- |
| Transient LOCK/LEARN/touch guard | Keep the latest eligible automatic intent pending; no Disconnect, repeated activation, error spam or retries until a guard transition permits commit. Direct APIs still raise. |
| Missing/invalid link, target-validation error, or domain activation failure | Clear the intent, latch its failure signature/reason and report once. Do not retry at 10 Hz. Retry requires a new selection event, explicit API request or explicit off→on; link edits clear stale failure/cache state but do not themselves route. |
| Activation failure with successful rollback | Restore the previous registry/context, watcher destinations and wire identities; keep the same MIDI child/ports and session. Controls remain gated until matching recall if reinstall invalidated acknowledgement; do not claim mapped readiness survived rollback. |
| Rollback failure | Report both failures and pause automatic activation. Gate affected input, preserve the MIDI child unless transport itself failed, and require explicit repair/Applybinding before follow can resume. Do not repeatedly attempt rollback or silently switch the persisted Follow toggle off. |
| Actual pipe/port/child failure | Retain the existing transport Disconnect/report behavior. Do not swallow transport failures inside a domain-error wrapper. |

Preflight failures must occur before destination registry/context mutation or destination-selection TX. Protective runtime fencing may already have happened at a hardware selection boundary; a later guarded retained-context resync can need corrective TX. A rejected TD-only request that never changed hardware context does not itself require fencing/resync. Post-mutation rollback may also need corrective announcements; tests must not claim zero wire traffic for these recovery cases. Capture/report unexpected follower exceptions once and pause the follower without masking a separately identified transport fault. No failed path writes target values or fires Pulse actions.

## Public interface and UI

| Proposed interface | Contract |
| --- | --- |
| `SetTrackComp(layout_id, track_id, comp)` | Validate and persist a Follow link. `None` unlinks it. Does not rename or rebind targets. Duplicate links in the same Layout fail before mutation. |
| `SelectComp(comp)` | Resolve exactly one linked Track in Active Layout and use existing selection API. Return selected context; fail clearly for missing/ambiguous links or guard rejection. |
| `GetCompContext()` | Detached snapshot of saved Follow preference, runtime status (`waiting_for_selection`, `waiting_for_editor`, pending, failed/paused or ready), observed/requested/routing COMP, source/sequence, connection generation, routing epoch/gate, linked IDs, pending reason and errors. |
| Binding / `Follow selected COMP` | One toggle (`Followcomp`): default off only when first created and in clean exports. Repeated upgrades preserve it. A saved True preference restores baseline-only waiting, not immediate routing. |
| Layout / `Focus COMP` | One OP reference (`Focuscomp`) for the active Track's link. Clear to unlink. Synchronize this field on context changes without generating another selection request. |

This adds two functional fields to existing pages, without another Binding mode or page. Put selection/pending status in the existing Inspector context/title; do not add public diagnostic parameters or new confirmation buttons. Label the link as Focus COMP so it is not mistaken for a restriction on all target destinations.

Do not modify unrelated parameter APIs. `Controlowner` is the active slot's owner, and `Targetowner` is the legacy single-target owner; neither becomes the routing-link authority.

## Source and persistence

Add `code/py/roto_python/text_comp_follow.py` with a `CompFollower` class. Keep TD pane sampling separate from link/intent decisions so ordinary Python tests can supply selection events. Runtime state belongs to the controller's follower instance, not module globals.

An optional Track `focus_comp` field belongs in the existing registry. Store a normalized relative path plus explicit `bound`/`missing` state; do not persist td.OP handles or OP.id as durable identity. Normalize/validate it during migration; absent links preserve all v1/v2 identities, target records and libraries. Repeated upgrades retain existing normalized metadata.

Within one extension lifetime, bind a live handle once. Rename/reparent retains that valid handle and refreshes its serialized path relative to the controller's current location. An invalid handle latches the link `missing`, invalidates cached lookup/pending intent, and never falls back to a new occupant of the same path. Delete+recreate and delete+undo both require explicit SetTrackComp/relink, even if undo produces a same-path COMP. Refresh valid handles before duplicate checks and any lookup so controller rename/reparent cannot reuse an obsolete reference basis.

At file reopen/reinit, resolve a saved `bound` path once and acquire a fresh handle; a `missing` link stays missing until relink. This is deliberately path-based across reload, not a globally stable COMP identity: replacement at the same path while the controller was not observing cannot be distinguished. Do not promise clone/replacement detection across a closed session. Explicitly report this boundary; do not write UUIDs/tags/storage into user target COMPs to expand the guarantee.

Save-time refresh is synchronous and independent of the timeline: extend the existing lifecycle Execute DAT with the documented `onProjectPreSave` callback, calling reference refresh/storage writes directly before project serialization, not a parameter pulse or next-frame task. Validate the native callback/signature on the target build. It refreshes all valid target handles against the controller's current path and persists missing state for invalid ones; it does not activate, send MIDI, alter Follow preference or run registration. Thus rename→immediate Save and timeline-stopped Save have explicit coverage. Before extension teardown, refresh references against still-valid cached handles before discarding them.

Managed component saves and the external export builder call the same private refresh routine before cloning/serialization. A project pre-save callback is not assumed to fire for arbitrary component `.save()` calls; native persistence fixtures must invoke the managed preparation. Unmanaged component saves without this preparation are outside the immediate-rename guarantee. Generic exports clear links regardless.

`RotoPythonExt` promotes the three APIs and owns the follower, connection generation and lifecycle invalidation. `layouts.py` owns saved link metadata, uniqueness checks, explicit guard outcomes and transaction/intent notifications. `collection_protocol.py`/`protocol.py` and FreeLearner integrate the control-plane-only transition fence so bypassing one dispatch path cannot write old targets or accept recall; feedback/deferred queues carry epoch/generation checks. `setup.py` builds the two UI fields; existing `parameter_callbacks` handles them. `lifecycle_callbacks.py` adds synchronous pre-save metadata refresh. Refactor Tick into bounded transport ingestion with synchronous selection-boundary fencing, selection observation/intent arbitration, one domain-isolated commit, then gated transport flush/publish; preserve disconnected observation without losing it at the existing early return. All cache invalidation and source generation changes must happen before another intent can commit.

Builders/upgrades install source before extension reinit, with repeated upgrade idempotence for links and Follow preference. Export embeds the helper, strips file dependencies, clears all Focus links with the registry, resets Focus COMP and Follow off, and retains disconnected startup. Do not publish user mappings in a generic tox.

## Operators, positions and data flow

| Operator | Type / family | Final position and size | Parameters / references |
| --- | --- | --- | --- |
| `text_comp_follow` | textDAT / DAT | X=540, Y=-740, W=130, H=90 | `language=python`; development `file=code/py/roto_python/text_comp_follow.py`, `syncfile=True`, `loadonstart=True`. Embed and clear these file references for portable exports. |
| Focus annotation | annotateCOMP / COMP | X=515, Y=-815, W=355, H=225 | Title `Focus`; contains the helper. No runtime role. |

The right-side temporary insertion slot, if needed, is DAT (1320, 0), with annotation (1295, -25, 180, 175). Use measured final geometry after creation. Final placement adds a Focus group after Guide in `cleanup_network.py`; a read-only dry run of the real planner produced (540, -740) and the annotation above, with every existing operator position unchanged. Prefer these verified final coordinates over leaving the new module at the insertion slot.

Position map: `{"text_comp_follow": [540, -740]}`. New group respects 25px side/bottom padding, 60px header clearance and existing group spacing.

Data flow:

`current Network Editor selection` → `CompFollower intent/link resolution` → `guard arbitration` → `Layouts.SelectTrack` → `existing MIDI recall/feedback`.

Use module references inside the controller and the existing `parent.RotoPython` shortcut for callbacks. No new signal wires, CHOP chain or in/out operators are needed. Preserve existing null endpoints. For operator installation, use the external builder contract; independent creation may be batched through `build_network`, with parameters verified by `get_help`. The new textDAT parameter names/`python` menu choice were checked during scout.

## Implementation phases

1. **Link model and API:** optional link migration, uniqueness, portable resolution and query contract. Add behavior tests before live installation; preserve full registry snapshots.
2. **Follower source:** explicit selected-set algorithm, pane/startup policies, single latest-intent arbitration, transition-fence and connection-generation contracts, guard/domain/transport failure classes and no-op behavior. Test logic separately from TD UI sampling.
3. **Infrastructure:** external builder/upgrade installs the helper and UI fields; update source-loading/export handling. Use the existing lifecycle and parameter callback DATs.
4. **Integration:** replace receive-loop unlock activation with one commit path, close the input/feedback fence synchronously at routing boundaries, add control-plane-only receive and generation-aware Connect/Disconnect/failure cleanup, isolate domain errors from transport fault handling, add synchronous pre-save reference refresh and extend Inspector status. Disconnect before dependency updates and extension reinit.
5. **Native verification and cleanup:** isolated linked two-COMP fixture, actual pane selection and native callbacks, reload/export checks, then review errors and actual geometry.
6. **Physical acceptance:** explicitly enable Follow on two suitable linked COMPs, verify A/B/A, locks and feedback. Save/export through live TD only after checks; no direct binary edits, commit or push.

## Verification gates

- Unit tests: link/unlink/cache invalidation, duplicate rejection without mutation, old registry migration, repeated upgrade retaining links and Follow=True, missing COMP, Active Layout scoping and repeated-selection no-op. Zero selected with current retained, sole selected COMP with different current, COMP+TOP and multiple COMPs have the exact candidate outcomes above.
- Arbitration tests: both TD→hardware→TD and hardware→TD→hardware while locked; exactly one activation after unlock; zero while LEARN/touch still guards; no fallback to an overwritten loser; explicit manual precedence; intent arriving during commit; buffered MIDI backlog; invalidation on link edit/unlink/context deletion/reload. Assert destination IDs and activation/TX counts, not just final labels.
- Transition-fence tests: mapped A with same-batch `select B → CC12 → CC44`, split CC halves across the boundary/backlog, button Toggle/Cycle/PUSH/Pulse press/release while fenced, gated mapping reports and unlock→input while LEARN/touch still guards. Assert zero old-target writes/Pulse calls, no target recall/FreeLearner assignment from fenced reports, no replay after commit, neutral pairing/edge state, and zero newly queued old feedback from edits/touch release/flush. Cover generation checks on controller-owned deferred actions and framing-safe handling of partially transmitted/received lines.
- Fence recovery tests: queued B→C→A, cancel/preflight failure, successful rollback and rollback failure; gates persist across backlog/Ticks, the original Track is not immediately made ready, and recovery requires a retained-context resync plus fresh matching recall. Explicitly verify locked browsing still permits authoritative locked-A input until unlock, and LOCK/LEARN/touch release packets remain processable while fenced.
- Session-lifetime tests: LOCK queues hardware B, Disconnect→Connect with the **same Layout manager**, then new handshake clears guards; B never activates. Repeat for child exit, pipe failure, failed opening, obsolete-generation callbacks and delayed pending work. Both sources' pending intents clear; old selected-track divergence/gates/readiness do not leak. New current-generation recall alone enables controls.
- Disconnected-Follow tests: cancel TD B pending at Disconnect; retain Follow preference with baseline-only waiting; a new offline C selection changes local context without TX/process start; reconnect recalls committed C rather than replaying B. A still-pending offline request is canceled by Connect, a fresh request during opening waits for that generation's readiness, and process/open failure cancels it while allowing subsequent new offline Follow.
- Failure tests: target preflight failure, post-mutation failure with successful rollback, rollback failure and actual pipe/child failure. Assert pending cleared/latched, no 10 Hz retry, previous identities restored where rollback succeeds, same child/ports preserved for domain failures, target input gated where required, and Disconnect only for actual transport failure.
- Lifecycle/pane tests: Follow=True reopen/reinit restores saved routing with baseline-only waiting; explicit off→on samples immediately; callback→parameter return waits; B pending under LOCK then Textport/pane close/changeType cancels TD intent; return establishes baseline and does not replay B. Revalidate pane state at commit, including before the next throttled sample.
- Identity tests: rename/reparent→immediate save, paused-timeline save, controller rename/reparent reference rebasing, deleted handle with same-path replacement, delete/undo requiring relink, and file reload acquiring fresh handles without depending on OP.id. Cover persisted missing state and the documented cross-reload path-based limitation.
- Regression: unchanged target/Plugin/device IDs, both pixelSortV3 Tracks and off-page Mix/Sortcrit definitions preserved. Existing eight-page library tests remain intact.
- Native fixture: ordinary COMP click, background click, box/mixed selection and current/selected disagreement; record actual currentChild/selectedChildren values. Select two real COMPs; verify context, no value/Pulse writes and no repeated registration/MIDI refresh while idle. Feed same-batch/backlog selection, unlock, CC and Pulse traces through the integrated receive path; observe actual TD parameter writes and Pulse callbacks over subsequent frames, plus fenced readiness/feedback. Exercise session cleanup with a retained Layout manager and stale-generation work. Test pre-save callback while paused and immediate rename/controller reparent→save→reopen. No explicit Follow link is assigned to the user's existing Tracks during implementation testing.
- Fast-switch regression: observable A→B→A and delayed mapping reports retain identities/page libraries and route only matching acknowledged targets. A selection reversal wholly between polls is not guaranteed to be observed. MIDI CC/mapping reports lack a context/session token, so these tests do not eliminate existing delayed-attribution ambiguity.
- Persistence: managed tox save/load and project reopen retain links and Follow preference, but not connected session/pending requests or live handles. Follow=True restores baseline-only waiting. Generic export reload has no Focus link, targets, file dependencies or MIDI process; Follow is off.
- Physical: A/B/A without re-LEARN, current parameter-to-motor/LCD feedback, reconnect, LOCK browsing/unlock following latest intent, LEARN/touch deferral and experimental reverse-direction loop prevention when that phase is added.
- Run `python3 -m unittest discover -q` from `src/touchdesigner` and `git diff --check`; never weaken either. Recheck live errors, cleanup containment and no overlap/backward connections. Record software/native and physical evidence separately in HANDOFF.

## Later experiment

Hardware Track selection can optionally select/reveal its linked COMP through the same Focus link. Default off. Apply only after successful routing; mark the selection source so the resulting TD UI event cannot feed back into another hardware selection. Do not move the user's pane when experimental mode is off or when the link is unavailable.

Names remain independently editable during this implementation. After acceptance, evaluate the requested Layout-name → Plugin-name synchronization using the settled Focus COMP/Track model.

## Review closure and primary references

The two P1 findings are addressed by the domain/transport failure boundary and single commit arbiter. The four P2 findings are addressed by the selected-set algorithm, baseline-only startup, explicit handle/save guarantees and cancel-on-pane-exit policy. Contracts are implemented; automated/native evidence is recorded in comp_follow_native_verification.json, with physical acceptance tracked separately.

The follow-up P1 is addressed by immediate boundary fencing of input, recall and feedback through backlog and recovery; the follow-up P2 is addressed by connection-generation stamping and explicit end/start invalidation for both intent sources, with newly initiated disconnected Follow retained. The original six findings can remain closed at the plan-contract level. These additional gates likewise require implementation and verification before acceptance.

- [Derivative COMP Class](https://docs.derivative.ca/COMP_Class): currentChild/selectedChildren are separate APIs; also checked against bundled 2025.33230 docs.
- [Derivative Getting started](https://derivative.ca/UserGuide/Getting_started): current/selected nodes and background-click behavior; native sampling remains required.
- [Derivative OP Class](https://docs.derivative.ca/OP_Class): OP.id lifetime and valid handles; also checked against bundled docs.
- [Derivative Pane Class](https://docs.derivative.ca/Pane_Class): pane identity, type and validity after close/changeType.
- [Derivative 2018.21150 release notes](https://derivative.ca/release/201821150): Execute DAT onProjectPreSave/onProjectPostSave callbacks. The tool catalog omitted save toggles, but native 2025.33230 introspection exposed projectpresave. Enable that parameter: an actual stopped-timeline project.save test verified the callback and immediate renamed-link serialization.

## Implementation evidence

192 automated tests pass, including integrated Tick backlog/partial-line epochs, button modes, fresh recall, rollback isolation, failed opening/pipe/child failure and UI rename recovery. Actual stopped-timeline project save/reopen retains renamed links, routing, preference and valid target without pending activation. Native fixture verifies actual current/selected disagreement, zero/mixed/multiple selection, no idle reinstall, actual parameter writes, Pulse once, boundary fences, guard release, session cancellation, offline Follow, repeated upgrade and managed tox reload. Actual project.save with the timeline stopped and Project Pre Save enabled verifies immediate rename serialization. Main registry identities, targets and off-page libraries are compared against live_select_before.json. Generic export/fresh builder and final errors/layout checks are recorded in the handoff. Ordinary mouse-click ergonomics, controller reparent stress and physical Follow A/B/A remain separate acceptance work; selected/current states were exercised through native API, not claimed as manual clicks.
