# ROTO-CONTROL Python handoff

## Current requirements and evidence routing

Use [AGENTS.md](../../AGENTS.md#change-scoped-validation) for validation requirements,
[CONTEXT.md](CONTEXT.md) for current architecture and [projects/README.md](projects/README.md)
for saved-project identity. Source baseline for this index: `2de08c9` (2026-10-12).
A source merge does not establish the embedded version of a saved `.toe`/`.tox`.

The entries below are chronological evidence. Read a claim with its date, source,
artifact and test method; later acceptance supersedes earlier pending wording only
for the same case. Historical resume steps, gates and “no commit/push” statements
are checkpoint records, not a new task queue or current authorization.
Owned Inspector/Snapshot integration, #15 validation changes and #3–#5 fixes have
later source/native/physical results below. Reuse their unaffected acceptance;
source tests and synthetic native messages do not establish physical acceptance.

## Unresolved limitations and deferred work

- Native Inspector/Popup drag deformation is deferred in issue #6; the user has
  explicitly put #6 on hold. It is not a blocker for unrelated changes.
- Other platforms, full-day reliability and USB hot-plug behavior are not broadly
  accepted. Only claim the environments and interactions actually recorded.
- Historical manual gates without a later matching result remain unproven in that
  scope. Investigate them only when the requested change depends on that behavior.

## Historical milestones

### First hardware milestone (2026-10-03)

First hardware milestone accepted on TD 2025.33230, 2026-10-03:

- Fresh Python host with no legacy host imports; physical MIDI uses a mido/rtmidi child process.
- Connected / PLUGIN handshake and mapping recall after reconnect pass.
- Correct LEARN order: enable LEARN, touch Knob 1, change Value in TD (or use Offer Value), exit LEARN. The user confirms LEARNED / Value. Mapping acknowledgement can arrive on leaving LEARN.
- Physical rotation delivers channel-16 CC12/44 and changes TD Value. Input-origin parameter callbacks suppress motor echo.
- Independent TD Value change from 0 to 0.75 sends motor feedback; user confirms physical motor movement.
- User confirms numeric LCD display after the touch/value-text fix.
- Thirteen protocol tests pass, including track context, returned mapping description, touch display, 14-bit pairing, display coalescing, echo suppression and touch deferral.
- Disconnect reaps the MIDI child process; the final live cleanup check passed in about 20 ms with no remaining process.
- `verification.json` captures the accepted connected session. `roto_control_python.toe` is the latest-project entry point; code remains in external synced files.

Value edits now auto-offer once per LEARN session. Hardware-origin callbacks are excluded; the manual Pulse remains repeatable. This addition is protocol-tested; a new physical LEARN acceptance is pending.

## Binding milestone (2026-10-04)

- Promoted BindParameter, BindCallback, SetValue and Unbind; target units, stable identities, range validation and mapping isolation.
- Two independent demo consumers; event-driven external parameter watcher; formal out_values CHOP output.
- Twenty-four automated tests pass. Live TD checks: external Speed edits, synthetic hardware parameter writes without motor echo, callback hardware event/software suppression, target deletion/mode suspension, callback failure, target rename resync and fresh builder reproduction. TD Collapse Selected reinitialized the controller during the reparent check; binding registration must be repeated after that workflow.
- Default Value mapping recall after reconnect still passes. Custom parameter binding physical LEARN and knob input passed (user confirmation); motor/LCD and reconnect recall also passed for the custom parameter target. Callback binding physical LEARN, hardware events, motor and LCD also passed; reconnect mapping recall passed for both targets. Software SetValue left callback Events unchanged. Cleanup reaped the owned process in about 40 ms. Synthetic messages are not physical acceptance.
- Saved component remains source-file/venv dependent. Callback objects and bindings reset on extension reload; startup registration is explicit.

## Historical limitations (2026-10-04)

Single-target mode is physically accepted. Collection supports up to 8 knobs/8 PLUGIN buttons in software; physical acceptance is in progress. No bank/page editor, MIX or transport controls. macOS was tested; other platforms are unverified. Numeric display is a temporary firmware overlay. No full-day reliability or USB hot-plug acceptance is claimed. Disconnect before source reload; extension reinit deliberately resets connection state.

TD 2025.33230 native MIDI receive defects are avoided through the external Python process, not fixed. No native MIDI operators are added to this project's user network. TD's system MIDI operators are unchanged.

## Historical resume steps (2026-10-04)

Open `roto_control_python.toe`, select `roto_python`, press Connect. Learned mapping should recall automatically. In collection mode inspect each base_targets/state row: aggregate Mapped stays false until all 16 configured targets are learned. If learning again, follow the ordered README steps. Disconnect before editing source. For another target, press the corresponding demo Use this binding. Saved Binding page setup is restored after initialization; temporary direct API registrations are replaced by that saved setup. Inspect diagnostics inside base_state or controller.State.

## Saved setup milestone (2026-10-04)

- Binding page stores mode, COMP/parameter handle reference, stable ID, label and range options; Applybinding applies it.
- Initialization defers restoration until the first Tick (or Apply/Connect), after promoted APIs are available. Connect remains manual.
- Callback mode runs internal registration.onRegister(controller); the supplied example registers callback_demo. The hook source is saved in the component and is preserved by upgrades.
- Outer diagnostics have moved to base_state. Public State returns a snapshot; output channel names remain unchanged.
- Thirty-two tests pass, including setup routing/invalid target/empty callback hook. Live extension reload restores both parameter and callback configurations; invalid setup fails closed and recovers after Apply.

Actual disk reopen verified for Callback mode in roto_control_python.5.toe: the hook recreated demo.callback.speed, Bindingvalid=True and Connected=False; pressing Connect recalled its hardware mapping.

Actual disk reopen also verified for Custom parameter mode in roto_control_python.6.toe: demo.parameter.speed restored automatically, Bindingvalid=True and Connected=False; Connect recalled mapping. Diagnostics remain inside base_state.

## Multiple controls milestone (2026-10-04)

- BindControls, target-ID SetValue/Offerparameter, fixed slot/hash acknowledgement, per-control pairing/touch/feedback and Toggle/Pulse adapters.
- Persistent internal targets table, 16 watchers, per-target state/RX tables, second out_controls endpoint. Only Groupid added to outer configuration; no outer diagnostics.
- 47 automated tests pass. Live TD synthetic verification: all 16 acknowledgements, interleaved Knob 1/8 input isolation, Toggle on/off, one Pulse action/count and no deferred callback duplication, 16 target-unit output channels, no errors.
- Synthetic verification is disconnected and does not constitute hardware acceptance. Knob 2 physical LEARN/input (10), motor/LCD (7) and recall accepted. Knob 8 LEARN/input (10) and motor/LCD (7) also accepted.
- Physical Button 1 Toggle RX 127/0/127 ends with TD True. Button 8 LEARN and three repeated positive CC27 messages produce exactly three actions. Physical Button 2 repeated positive CCs produce exactly three Pulse actions after rearming; user confirmed LEARNED. LED state observation is not separately accepted. Existing single-target hardware acceptance is retained.

Pulse metadata now uses Ready/Trigger. Re-LEARN Button 8 refreshed cached firmware labels; user confirmed Ready. Button resets immediately; a nonblocking 0.3-second LCD Trigger flash then sends Ready. Middle slots are software-tested, without individual physical LEARN acceptance. Hardware tests recorded in controls_verification.json. Saved as roto_control_python.7.toe; canonical entry point has identical SHA-256. Actual disk reopen restored all 16 targets and 16 output channels, Bindingvalid=True and Connected=False. Connect recalled the five physically learned controls: Knob 2/8 and Button 1/2/8. Remaining configured controls require individual LEARN before use.

Physical LCD limitation: after re-LEARN the user confirmed Ready, but only Ready was visible on press. The host sends Trigger followed by Ready after 0.3 seconds; a visible Trigger overlay is not accepted on this firmware. Pulse counts remain correct.

Final saved setup: roto_control_python.8.toe (latest canonical entry point matches bytes). Actual disk reopen restored 16 targets, startup disconnected, and all five learned controls recalled after Connect. Final live TD remains open/disconnected.

Ableton reference check at commit 2d43a72: plugin buttons connect to Live parameters. LCD reads param.str_for_value(param.value), with value-change throttling/trailing refresh. Learn quantized strings are zero-filled. The TD Pulse reset and timed Trigger/Ready text are our adapter behavior; no equivalent generic Pulse/flash exists in the reference script.

## Pulse LED feedback revision (2026-10-04)

User chose button LED feedback instead of text changes. Pulse now emits LED 127 immediately, then 0 after 0.2 seconds via the existing Tick/flush path. Business action remains immediate and its value/output remains zero. Either latched input value fires, so pressing while LED is lit does not lose the zero-valued press. Per-button deadlines extend on another press and reset with the session. LCD/learn labels are both Ready. Old cached labels require one re-LEARN. 49 tests pass. User accepted short LED flash and fixed Ready LCD. Button 8 count progressed 0 → 3 → 6 with all six hardware presses received. The final three RX messages were CC27=127, about 0.233 seconds apart; the zero-valued press during the 0.2-second LED hold is automated-test coverage, not a physical acceptance claim. No new operators/custom parameters.

All 16 Parameter Execute OP expressions now return str(OP), resolving the correct target in TD 2025.33230. A fresh builder was verified after watcher initialization: hardware Pulse acknowledgement clears, and a later software Pulse in LEARN offers metadata. Native TD Pulse callbacks can coalesce multiple pulses in one frame; use Python callback bindings when every same-frame event must invoke business logic separately. Saved LED revision: roto_control_python.9.toe.

## Compact numeric LCD (2026-10-04)

Single Value, parameter/callback and collection numeric formatters share three-decimal rounding with trailing zeros removed. Toggle/Pulse labels remain On/Off and Ready. TD target precision is unchanged. 50 tests pass; live collection formatter verified 0.123 and 7, and all five learned mappings recalled. Saved as roto_control_python.10.toe.

## Component interface and reusable export (2026-10-04)

Registration hook (legacy menu value callback) restores parameters, callbacks and mixed collections. GetValue/GetControlState provide per-target snapshots without table parsing or new status custom pars. Unknown single-target IDs are rejected. Unbind now uses the common three-decimal formatter. 55 tests pass. Nested/renamed parent and mixed-registration tox reload passed; synthetic Pulse callback and software no-echo passed with target precision retained. Export embeds TD DAT code, strips demo configuration and fixes same-machine Python/Helper paths. External MIDI dependencies are still required. Saved project: roto_control_python.11.toe.

## Native TOGGLE feedback (2026-10-05)

User edited Button 8 step labels in Roto-Setup: zero Ready, 127 Trigger, TYPE TOGGLE, two steps. Chose to retain TOGGLE and remove TD LED timeout. Pulse actions still accept both latched values; firmware controls LED/step labels. TD sends matching latched CC and Trigger/Ready display feedback immediately, with no timed reset. Recall initializes state zero. New learn metadata is Ready/Trigger. Hardware PUSH remains a separate future input adapter; no PUSH mode change was made. Software tests verify no timed/per-press output and preserved action counts.

No-feedback trial: four RX messages (127, 0, 127, 0) produced count 44 → 48 with TX fixed at 64. User reported only Button 8 label and no lit LED; native rendering without host feedback is not accepted. Revised to echo each accepted latched state immediately, with no timer/reset and no Pulse display-text command. CC-only trial: two presses produced count 48 → 50 and TX 64 → 66; LED lit/dim was accepted, but LCD remained Button 8. Added matching immediate Trigger/Ready display feedback to the same latched state; still no timer/reset. Final state+text version accepted: user confirmed Trigger/light and Ready/dim. Count 53 → 58, TX 74 → 84: five additional actions, two immediate feedback messages per action, no timeout. Saved as roto_control_python.12.toe; reusable export refreshed.

## Whole API sequence review (2026-10-05)

- Shared Toggle dispatch now confirms committed state with immediate CC and display feedback for parameter and callback targets. The former knob echo acknowledgement suppressed button LED confirmation.
- Added explicit button_type (toggle default / push), independently of TD toggle/pulse action. Native TOGGLE Pulse accepts either latched press value; PUSH Pulse accepts only rising presses and confirms release. No feedback timeout. User-owned targets table gains an optional button_type column; 17 outer custom parameters retained.
- Collection software failures now suspend/report only their target. Global saved registration failures correctly invalidate all query snapshots; Applybinding recovers.
- 62 automated tests pass. Live disconnected mixed six-target fixture passed mapping, metadata-only LEARN, precision, callback echo suppression, Toggle confirmation, paired knob input without motor echo, PUSH press/release filtering, native deferred Pulse exactly once, per-target failure/recovery, reinit and tox saved-hook reload. No operator errors.
- Main 16 targets / 16 output channels restored; Button 1 recalled. Physical Button 1 Toggle LCD/LED accepted: On/light then Off/dim. Button 8 PUSH hardware acceptance completed; see PUSH milestone below.

Disk reopen additionally reproduced stale watcher OP cache: Controlowner resolved but watcher.op remained None when its identical expression was reassigned. Restore now clears/reassigns the expression; all 16 watcher OPs resolve after reinit. A direct demo Knob1 parameter edit is checked against GetValue on the following frame. Final save follows this correction.

Button 1 physical acceptance completed on .14 runtime: latest CC20 RX 127 then 0 (about 1.716 seconds apart), final TD value 0, mapped/valid True. User confirmed On/light → Off/dim. Aggregate RX/TX include other controls and reconnect, so they are not treated as per-pair feedback counts.

## PUSH hardware milestone (2026-10-05)

- User changed Button 8 hardware TYPE to PUSH; Roto-Setup does not expose step labels in PUSH mode. TD targets table declares button_type=push, mode remains pulse.
- Six CC27 127/0 pairs produced exactly six actions: count 170→176; release does not fire. Includes two short presses and four holds (about 1.27–2.12 seconds), no hold repeats. TX 68→92 matches CC plus display confirmation for all twelve transitions.
- User accepted held LED bright / released dim. LCD text was not separately specified, so text acceptance is not claimed. No runtime errors; mapping recalled without LEARN.

## Mapping Inspector (2026-10-05)

- Internal inspector Container uses cloned built-in Lister with external listerConfig, 19-row column definitions and read-only target table. Live build uses textCOMP looks (TD 2025.33230). No outer custom parameters added.
- Public GetControlStates and destination fields in GetControlState provide detached snapshots: parameter owner COMP path/name, callback classification and built-in Value destination. Inspector never changes bindings or opens MIDI.
- 64 automated tests pass, including UI observer failure isolation from hardware host. Live mixed six-target Inspector passed parameter/callback destination display, deferred native Pulse, deleted target Invalid/Unavailable plus error, unaffected callback, and Unbind to single built-in Value. Main 16 acknowledged controls render in screenshot, with Button 8 Pulse/PUSH.

Fresh source builder verified default Value Inspector and switching to saved 16-target collection. Inspector is an optional observer; refresh errors are shown in its title/storage without suspending transport.

## Clear Learn (2026-10-05)

- Per-row Clear Learn button and public ClearLearn(id) use SysEx PLUGIN 0E: F0 00 22 03 02 0B 0E CT CI F7 (official v1.6 section 3.14, PDF page 23). Current-page control only; preserves TD registration/value and all other mappings. This is an outgoing-only command, with no acknowledgement.
- Guards: connected PLUGIN, exit LEARN, release selected knob; no callback recursion. Clear pending half-pairs/deferred/display state and Pulse latch. Failed send preserves mapped state. Optional UI reports rejected actions without suspending targets.
- 67 automated tests pass. Live disconnected six-target fixture exercised actual Lister external onClick callback, exact Button 8 unmap bytes, per-target isolation, ignored unmapped input, LEARN rejection and re-LEARN. No operator errors.
- Main demo hardware mappings were preserved during implementation. Physical unmap persistence remains unverified until the user clicks Clear and confirms reconnect does not recall that control.

## Mapped COMP tags/color (2026-10-05)

- Parameter destination COMPs with valid acknowledged mappings receive roto_mapped tag and cyan node color (0.20,0.55,0.70). Callback targets do not infer a destination. No outer status parameters added.
- Destination ownership supports several mapped controls/controllers, original color/tag restoration, rename and manual color preservation. Last clear or Disconnect releases only that controller's claims. Optional marker errors are recorded internally without stopping hardware dispatch.
- 71 automated tests pass. Live isolated mixed registration confirmed tag remains after clearing the first two parameter mappings, then disappears/restores original color after the third/last; user_tag and callback mappings remain intact. Main mapped demo COMP tag/color accepted by live inspection.

Clear Learn persistence confirmed after user action: fresh Connect recalls the other 15 controls but not demo.button8; count stays 186. Latest UI status was an offline rejection, so the exact earlier successful unmap TX/press sequence was not captured and is not claimed. Ableton script at reference commit defines UNMAP_CTL=0xE but AST has no loads of that symbol or literal command-14 _send_sysex call. TD ClearLearn is a wrapper around the ROTO SysEx command.

## Inspector active mapping projection (2026-10-05)

User clarified Clear Learn should clear displayed destination, rather than only flip Mapped. Inspector now shows COMP/Parameter/Value only for valid mapped controls; cleared/invalid rows show —. ID/action/hardware configuration remain, and API registration/value are retained for re-LEARN. Regression tests reproduce old stale-looking destination and cover restore after remap plus callback/invalid rows.


## Inspector confirmation and target editing (2026-10-05)

- Per-row Clear now renders distinct Yes/No buttons inside the same cell. External list_events forwards native Lister callbacks without changing cloned internals and captures cell-local release coordinates. Clear All has its own Yes/No toolbar confirmation. Stale configuration/connection confirmations expire.
- Min/Max remain visible for registered unmapped targets; double-click editing uses ConfigureControl for range, button Mode and hardware adapter. Native style/clamp constraints enforced; callback Toggle/Pulse switches supported. Value uses SetValue; Pulse Value and fixed button bounds are read-only.
- Changed target configuration persists in control_overrides storage and sets requires_relearn; row amber / Error Needs re-LEARN until matching acknowledgement. No-op or invalid edits preserve mappings. Clear All preflights all controls; transport failures can still produce partial completion.
- 81 tests pass. Live synthetic fixture passed native Lister edit and Yes/No click routes, toolbar cancel/accept, style rejection, precise range preservation, per-control isolation, reload of saved overrides and pending re-LEARN, highlight and acknowledgement clearing. Main hardware mappings were not cleared during these tests.


## Inspector interaction correction (2026-10-05)

Mode is now a single-click Toggle/Pulse popup menu with the current item checked; native style validation remains in ConfigureControl. Clear cells dispatch once per native release and bypass cloned Lister selection/double-click bookkeeping, preserving two-click Clear→Yes/No despite intervening confirmation refresh. Fixed readonly-cell initialization accidentally placed under onDoubleClick. 84 tests pass; live synthetic native events verified first click only requests confirmation, second clears even with native click=2/inside=0, and popup selection updates callback Mode with Needs re-LEARN. Physical mappings were not cleared by implementation tests.

## Persistent Inspector and target deletion (2026-10-05)

Current behavior supersedes the earlier active-only projection and UI hardware-only Clear. The Inspector reads a stored catalog, retains registered data on Disconnect, and presents all 8 knobs + 8 buttons on All COMPs / individual COMP / Python callback pages. Missing/removed slots show Unassigned.

Clear/Yes deletes the record and routing; Clear All removes every registration. Offline removals queue hardware unmap for PLUGIN readiness. Saved-hook restore filters removed IDs, stale acknowledgements cannot restore them, and explicit public registration opts an ID back in. ClearLearn remains available as the separate hardware-only API. Mode uses native release → popup → ConfigureControl → refresh, with incompatible native parameter modes disabled. Source Unicode symbols use ASCII Python escapes to survive TD external text loading.

90 automated tests pass. Live TD synthetic checks cover six-target API sequence, Disconnect catalog, COMP pages, empty 16-slot projection, row removal and Clear All, saved-hook filtering, reconnect unmap bytes, reinit empty restore, native popup selection, two-click Clear and built-in single Value removal. Main hardware mappings are preserved; this revision's physical deletion was not exercised on the user's controls.

## User COMP integration (2026-10-05)

`pixelSortV3` and `fractal_pop` are now the saved 13-target collection; the user had cleared all prior demo bindings before this run. `scripts/real_component_setup.py` is the reproducible installer. Eight numeric targets, three Toggle targets and two Pulse targets span both Inspector COMP pages. Slots 5–7 buttons stay Unassigned; no functional operators were added inside the user's COMPs.

API now supports writable same-style Par BIND chains ending at CONSTANT masters. Expressions/exports/readonly roots, missing/cyclic/non-Par masters and shared aliases are rejected, and all numeric clamp limits are validated. Target aliases retain their BIND mode/expression. 95 automated tests pass. Live `diagnostics/runtime/verify_real_components.py` verified real software writes, public/master edits, all 13 synthetic mappings and input, Int rounding, camera bound Reset exactly once and both Pulse watcher acknowledgements, node marks, pages, Disconnect catalog, deletion/restore and empty Clear All. Original target values, camera transform/pivot and the temporary Reset observer were restored. Physical LEARN acceptance remains pending.

## Inspector Learn action (2026-10-05)

Added Learn/Re-learn column to the existing native release action path. The row calls Offerparameter(id), with connected PLUGIN / valid target / LEARN guards and a status message. No implicit registration, value write, Clear or success flag. Empty slots have no action; double-click callbacks cannot send a duplicate. 99 tests pass; native release synthetic checks verify exact target hashes and one command-0A metadata packet for knob, parameter Pulse and callback Pulse, without executing actions. Matching acknowledgement changes the label to Re-learn. User physically confirmed LEARNED / Low Threshold after the first Knob 1 offer; rotation/motor verification remains pending. Inspector rebuild reinitialized the TD session, so hardware recall is checked after final Connect.

## Button 8 hardware TYPE correction (2026-10-05)

User clarified Button 8 currently behaves as a latched TOGGLE: Ready/dim and Trigger/light alternate. Its TD action remains Pulse. The earlier real-COMP setup incorrectly declared PUSH, which ignores alternate zero-valued latched presses. Corrected the saved table/installer/override to TOGGLE; no LED timeout is added. The temporary LED TX probe was removed.

ConfigureControl now separates input-adapter-only edits from changes to wire range/mode. Adapter-only edits keep the same target object/hash/mapping/LED state, issue no unmap/metadata, persist the override, and retain any existing Needs re-LEARN flag. 101 tests pass, including preserved latched state and PUSH release semantics after an adapter switch.

Physical Button 8 acceptance after reopening .25: four distinct CC27 events (127, 0, 127, 0) produced exactly four native Clearhistory Pulse dispatches. Three presses were requested, but four actual events arrived; there was no extra dispatch per MIDI event. Mapping stayed valid, Pulse value stayed zero, native pulse acknowledgements were consumed, and no operator errors were reported. Temporary action-count probe was removed. Evidence: button8_toggle_acceptance.json.

## TOGGLE Pulse immediate reset (2026-10-05)

User requested retaining hardware TOGGLE but immediately returning Pulse feedback to idle. Common CollectionHost RX now sends CC=0 and Ready immediately after each accepted TOGGLE Pulse action; PUSH keeps its press/release state. 101 tests pass, including immediate reset, alternating zero presses and repeated positive presses. Live isolated common-path check passed; main Button 8 mapping recalled without re-LEARN and no operator errors. Physical LCD/LED acceptance is pending. This supersedes the latched-feedback behavior above.

## Button 8 PUSH selected (2026-10-05)

User selected hardware PUSH instead of TOGGLE immediate-reset feedback. Updated adapter and real-COMP installer to PUSH. After reconnect, three physical press/release pairs (CC27 127/0) dispatched exactly three native Clearhistory actions; release dispatched none, acknowledgements consumed, mapping valid, no operator errors. Temporary action counter removed. Evidence: button8_push_acceptance.json. Press duration was about 0.1 seconds; held LCD/LED appearance was not explicitly confirmed by the user.

## Free COMP assignment (2026-10-05)

Added Inspector COMP/Parameter pickers and public AssignParameter(kind, slot, parameter). Compatible Float/Int or Toggle/Pulse parameters are discovered on demand in the parent project branch. Mode/label/range/ID are inferred; registration persists in parameter_assignments and overlays the saved table/hook on restore. Other collection target objects/mappings remain intact. During hardware LEARN, choosing a parameter automatically offers once. No user table/script editing or Applybinding step. Hardware TYPE remains declared independently.

109 tests pass. Live isolated new-COMP checks passed discovery, one offer during LEARN, mapped-slot replacement with unrelated mapping preserved, stale identity rejection, numeric hardware input/software feedback, inferred Toggle/Pulse, Disconnect catalog, extension reload, removal without resurrection and clean errors. Temporary COMPs were removed. Physical LEARN acceptance for the new picker remains pending.

Embedded export .15 additionally passed discovery of a new COMP, first auto-offer during LEARN and actual assignment save/load through a temporary .tox file. Native COMP and deferred parameter popups were rendered and checked. Temporary holder/tox removed. Canonical reusable export promoted to .15.

Saved as roto_control_python.27.toe; canonical project bytes match. Final Connect recalled existing Knob 1/8 and Button 3/8 mappings; Button 8 remains Pulse/PUSH. New picker physical LEARN is pending user selection.

## Direct new-COMP slider LEARN (2026-10-05)

User clarified the required workflow is hardware LEARN/select control -> change any new tool custom parameter, with no Inspector assignment. Added FreeLearner and one internal Parameter Execute DAT active only in connected PLUGIN LEARN. Unregistered parameters are offered with an independent parameter index; matching CONTROL MAPPED index/hash commits the hardware-reported slot. Other targets/mappings stay intact. Saved UI assignment records now preserve the dynamic wire index. Duplicate slider updates, API SetValue echoes and control business actions during LEARN are suppressed. Expression/export/readonly sources and controller internals are excluded.

116 unit tests pass. diagnostics/runtime/verify_free_learn.py exercised an actual unregistered new COMP Par change through native onValuesChanged, then simulated matching hardware slot acknowledgement, numeric input, preserved unrelated mapping, observer shutdown, API-write exclusion and extension reload with dynamic index retained. An initial same-frame watcher setup/change missed the callback; the actual verification now initializes observation for one frame before changing the parameter, matching hardware LEARN followed by slider interaction. Temporary fixture removed. Physical direct learn is pending user test on sortError.

Fresh embedded export .16 passed native unregistered slider callback, hardware-acknowledged Knob 5 assignment, unchanged device identity through first single-to-collection promotion and actual temporary .tox save/load with index 128 retained. Temporary probe/tox removed; canonical export promoted to .16.

Saved .28.toe (canonical bytes match) and reconnected: original Knob 1/8 and Button 3/8 mappings recall. sortError is discoverable; observer is disabled outside LEARN. Ready for physical hardware LEARN -> select knob -> change sortError custom Float, without Inspector interaction.


## Physical direct free-learn acceptance — feedback

User added feedback and selected Knob 2. Live hardware CONTROL MAPPED acknowledgement committed feedback.Opacity at dynamic index 129 without Inspector registration. TD parameter and mapped state both read 0, range 0–1; feedback has roto_mapped tag and cyan mark. Rotation/motor acceptance is still pending. This assignment was added after the .28 save and has not yet been saved to disk.

User confirmed Knob 2 rotation changes feedback.Opacity; live value read 0.007 after rotation, Mapped=True and no target error. Motor feedback for this target has not been physically tested.

Saved feedback COMP and Knob 2 assignment to roto_control_python.29.toe; canonical project SHA-256 matches.


## Portable tool cleanup

Live workspace already contained only roto_python and no user target COMPs when cleanup began. Removed six optional outer CHOP output nodes; retained target/callback API, Inspector and required internals. Layout verified across 4 networks, 17 groups, 61 operators: containment passes, no overlaps or backward wires.

MIDI helper is embedded as midi_process and launched via Python -u -c; legacy Helper file fallback is retained. Generic export starts as an empty collection with 16 Inspector rows, not the old Value target. Nested/renamed tox reload completed actual hardware PLUGIN handshake with an invalid external Helper path and zero DAT file dependencies. Native new-tool parameter edits offered correctly; synthetic Knob 2 acknowledgement and SetValue write passed. 116 tests pass; hardware rotation after this packaging change was not repeated. Performance snapshot shows initial ListerExt compile at 8.07 ms, cooked once and idle at inspection; continuous performance under load is not claimed.

Final export: exports/roto_python.19.tox; canonical exports/roto_python.tox matches SHA-256. Project saved as .30.toe; canonical project bytes match. Main instance is embedded, empty and disconnected.


## Repository migration

Authoritative workspace: /Users/huihongnin/project/roto_control/src/touchdesigner, origin https://github.com/joshuahhn/roto_control.git. Original nin-lab folder is retained as migration backup; continue all edits in this fork. Local docs helper is scripts/td_project_docs.py. Runtime environment is recreated here; do not use the old nin-lab Python path. Historical Backup, crash saves and older binaries remain at the original location.

Migration verified: current live TD project is roto_control_python.32.toe under the fork. Canonical toe and tox hashes match latest .32 / .20 versions. New local Python environment completed actual hardware handshake. 116 tests pass; no live errors. No commit or push performed.


## Menu parameter mapping

Shared binding/controls/free Learn/Inspector now support custom Menu targets: knobs select quantized indices; buttons use Cycle with wrap. Label feedback and wire identity include choice semantics; options changes suspend old bindings. 123 tests pass. Live native Menu callbacks offered both knob/button targets; synthetic acknowledgements, knob CC input, PUSH press/held/release routing, API writes and assignment reload passed. Physical Menu LEARN/feedback remains pending. Existing user pixelSort mapping is preserved. Temporary fixture removed, final errors clean.

Saved .33.toe and exported .21.tox; canonical files match. Clean exported tox reload supports both Menu knob/button assignment and option-label API feedback. Main hardware handshake and existing pixelSort Knob 1 recall verified. No fixture remains.


## Physical two-option Menu LEARN

User reported the first Masksource attempt did not show LEARNED, then confirmed retry worked. Actual hardware acknowledgement maps pixelSortV3.Masksource to Knob 3; Mapped=True, Valid=True, choices source/control, range 0–1, no error. Two-option Menu LEARN is confirmed; physical Knob 3 rotation has not been independently confirmed. The initial missed LEARN was not reproduced or root-caused; no additional runtime fix was made. Temporary diagnostic fixture removed. Saved .34.toe with this assignment; canonical toe SHA-256 matches. Generic export .21 remains empty of user assignments.


## Inspector Annotation filtering

COMP picker excludes annotateCOMP and stops traversal into its internal network, for both knobs and buttons. Live list previously contained seven annotations; after source reload both lists contain pixelSortV3 only. Direct eligible_parameters also rejects annotateCOMP. 123 tests pass. Exported clean .22.tox and promoted canonical tox; main reconnected and saved .35.toe with existing user mappings retained. Canonical toe hash matches.

## Layout phase 1 — fixed display names (2026-10-06)

Display page now has Trackname=EFFECT and Pluginname=CUSTOM. SetLayoutNames validates at most 12 printable ASCII bytes, rejects edits during hardware LEARN and updates current track/name metadata without DAW SELECT, unmap, identity changes or mapping-state resets. Invalid native edits restore the previous accepted name and retain a visible internal Lasterror. Fresh source builder and upgrade callback allowlists include both names. Collection replacement preserves accepted display names. Generic export resets names to EFFECT/CUSTOM.

131 automated tests pass, including exact metadata-only packets, atomic validation/LEARN rejection and isolated probe routing guards. Live embedded source update verified native invalid-edit rollback/error after a subsequent tick, names preserved through BindControls, restored defaults, promoted API and clean TD errors. Current collection remains empty with existing deletion tombstones/pending unmaps preserved. No registry/UI has been built.

External diagnostics/runtime/layout_protocol_probe.py and LAYOUT_PROBE.md prepare the A/B/A hardware gate. Probe has its own MIDI lifetime, distinct synthetic identities, ordered RX/TX log, requested versus control-confirmed state, lock/LEARN/touch guards and no UNMAP/user-target writes. It has not been started and physical recall remains unverified. Production TD must be disconnected before probe port ownership; stop/close ports then reconnect production to restore.

Phase-1 artifacts saved through live TD as .36.toe (canonical SHA-256 matches) and clean reusable .24.tox (canonical promoted); export reload verified default names, updated embedded protocol/docs, empty assignments/pending unmaps and no MIDI process. Main production session was reconnected; physical display appearance and A/B/A recall are still awaiting user confirmation.


## Layout hardware gate (2026-10-06)

Isolated A/B probe confirmed distinct plugin/parameter hashes recall A -> B -> A after reconnect without re-LEARN. B received 75 physical inputs in session2; A received 35 after recall in session3. Hardware LOCK event caused local select B rejection with no selection TX or active-state change; unlock event received. User confirmed PROBE EMPTY display and previous label cleared; EMPTY remained unacknowledged and input-disabled. Returning from EMPTY received matching A acknowledgement. Probe stopped and production TD Connect requested. Evidence: layout_hardware_verification.json. Hardware-origin selection under lock and delayed-CC attribution remain unverified; no general selection-complete acknowledgement was inferred.


## Saved Layout registry and UI (2026-10-06)

Implemented persisted parameter Layouts, Layouts page selection/create/rename/delete confirmation, per-Layout display names, missing-target catalog and active-only Clear. Switching reads current parameter values without firing Pulse actions. LEARN/touch/LOCK guards and matching control recall gate routing. Capacity is 8 Layouts. Callback registration remains a separate legacy mode; its registry survives callback Applybinding/reinit and returning to a saved Layout.

139 tests pass. Native verification covered callback mode/reinit/return, two-Layout tox save/reload, disconnected empty generic export and embedded source. Network cleanup checked 4 networks, 17 groups and 63 operators with containment, no overlaps or backward wires. Temporary verification COMPs removed; production handshake Connected=True/Plugin=True, empty Custom Layout and no Lasterror. Stale hardware mapping reports are rejected because no corresponding target is configured. Evidence: layout_native_verification.json and layout_hardware_verification.json.

Final artifacts: project .37.toe and generic export .26.tox (documentation refreshed after .25 verification). Canonical copies match numbered artifacts. Final production Layout UI physical acceptance remains pending; isolated A/B/A hardware recall and lock/unlock passed. Hardware-origin selection under LOCK and delayed CC attribution remain limitations. No commit/push.

## Multi-Track build awaiting physical acceptance (2026-10-06)

User authorized building while away and reserved hardware tests for their return. Verified live .37.toe in this repo, then disconnected and saved .38 as baseline. The live configuration had Custom and an additional user-created T Layout; both migrated independently to registry v2 without changing group/device identities or removal records. Baseline retained as roto_control_python.pre_multitrack.toe (copy of the live-saved .38).

Implemented Layout -> Tracks -> Plugin -> mappings in existing Python DATs. One Plugin per Track in this release, nested Plugins list retained. Track CRUD and native Tracks page, paged Track announcements, hardware-origin Track selection, TD-origin Track sync, independent same-name Plugin identities and Plugin-scoped Inspector/clear confirmations are implemented. Layouts no longer occupy hardware Plugin entries and no longer have an eight-item cap. Under LOCK, hardware-selected Track can differ from routing Track; unlock follows selection. This lock behavior is software-tested only, not physical acceptance.

Migration preserves v1 Layout IDs, target wire hashes/indices, settings overrides, tombstones and pending unmaps. New Track identities are independent. Switching reads current values, never restores numeric presets or fires Pulse. Callback hook mode remains separate. Two native integration fixes were included: formatter import resolves at binding DAT module initialization, and deferred display callbacks do not overwrite a newer Track menu choice. Rollback retains the transport session while requiring mapping reconfirmation.

154 automated tests pass. Disconnected native fixture verified same-name Track isolation, Inspector context, clear-confirmation expiry, synthetic Track selection/mapping/input, native Track dropdown and New Track pulse, and actual tox save/reload with identities/assignments preserved. Fresh builder passed. Generic export reload verified one empty Layout/Track/Plugin, no assignments/deletion records, no external DAT file dependencies and no MIDI process. Evidence: multitrack_native_verification.json; repeatable native stages: diagnostics/runtime/verify_multitrack.py. Native synthetic input is not physical acceptance. Fixtures removed; network check covers 4 networks, 17 groups, 63 operators, with containment and no overlap/backward wires.

Prepared artifacts: project .40.toe and generic export .27.tox, with canonical copies. Final controller is disconnected on the user's T Layout; no hardware LEARN, motor or reconnect probe was run. No commit/push.

On return: connect manually, use Tracks / New Track name + New empty Track to create a second Track within a chosen Layout. Learn the same knob slot to different test parameters in both Tracks, keeping Pluginname=CUSTOM. Test hardware and TD A/B/A, current values/motor/LCD, reconnect, empty mappings, LOCK selection/unlock and ninth-Track paging. Layout selection remains in TD. Do not treat old two-Plugin probe evidence as multi-Track acceptance. MIDI CC and mapping reports lack a Track/session token; delayed-event ambiguity remains documented.


## Physical multi-Track A/B/A acceptance (2026-10-07)

User confirmed Knob 1 controls pixelSortV3.Sortcrit on Track T and pixelSortV3.Lowthresh on Track TRACK, both Pluginname=CUSTOM within Layout T. User confirmed switching back and forth recalls independent mappings without re-LEARN ("working, pass"). Live inspection observed Sortcrit Mapped=True after return to T; both Plugin identities and target records were present. Evidence: multitrack_hardware_verification.json. Reconnect, motor/LCD, LOCK and ninth-Track paging remain pending.

Saved both mappings through live TD as roto_control_python.41.toe; canonical project matches. Existing connection retained. Generic export remains empty .27.tox. No runtime source changes, commit or push.


User additionally confirmed Disconnect -> Connect works (2026-10-07). Live inspection after the report: Connected/Plugin/Mapped=True on TRACK / CUSTOM, Knob 1 -> pixelSortV3.Lowthresh, requires_relearn=False, no Lasterror or operator errors. Reconnect recall accepted; motor/LCD, LOCK and ninth-Track paging remain pending. No additional project save or runtime changes needed for this verification.


User confirmed motor movement and LCD feedback after editing Lowthresh in TD on TRACK (2026-10-07). Live inspection remained connected/mapped with no Lasterror; value at inspection was approximately 0.667, so exact 0.8 positioning is not claimed. Physical parameter-to-hardware feedback accepted for this target. LOCK selection/unlock and ninth-Track paging remain pending.


User confirmed LOCK blocks TD-origin Track switching (2026-10-07). Live inspection retained TRACK / Lowthresh Mapped=True and Lasterror="Unlock hardware before switching Layout". Lock was already off at inspection; this records the user-confirmed guard, not hardware-origin selection under lock. Hardware-origin Track selection under LOCK/unlock follow and ninth-Track paging remain pending.


Hardware-origin Track selection under LOCK accepted (2026-10-07): user confirmed operation; live inspection showed locked=True, selected Track T, routing Track TRACK, and Knob 1 still mapped to Lowthresh (value approximately 0.326). Unlock-follow and ninth-Track paging remain pending.


Unlock-follow accepted (2026-10-07): user confirmed Knob 1 returns to Sortcrit without re-LEARN. Live inspection showed locked=False, selected/routing Track T, Sortcrit Mapped=True, requires_relearn=False, value 4 (Red), no Lasterror. Multi-Track A/B/A, reconnect, Lowthresh motor/LCD feedback, TD-origin lock guard, hardware selection while locked and unlock-follow are now physically accepted. Ninth-Track paging remains pending.


## Physical ninth-Track paging acceptance (2026-10-07)

Temporary Paging test Layout contained nine empty Tracks. User confirmed PAGE2-09 visible on hardware page two. Live inspection after browsing showed first_track=8 with PAGE1-01 still active, proving page browsing did not select a Track. User then selected PAGE2-09; live inspection confirmed matching selected/routing Track, page index 8 and no errors. Empty Track selection is accepted without inventing a mapping acknowledgement.

Temporary Layout removed, original T Layout / T Track restored with Sortcrit recall. Saved through live TD as roto_control_python.42.toe; canonical bytes match. User mappings retained, connection remains active, generic export unchanged. All enumerated physical checks in multitrack_hardware_verification.json have now passed; delayed MIDI attribution remains a protocol limitation. No commit/push.


## Plugin control-page overwrite fix (2026-10-07)

User reported that learning T/CUSTOM Page 2 Knob 1 removes Page 1 Knob 1, and clarified the requirement is eight control pages per Plugin. This is distinct from the previously accepted Track-list paging. Reproduced in FreeLearner/AssignParameter: the slot-keyed overlay tombstoned the previous parameter. Live trace control_page_trace.json shows GENERAL left/right 14/15 followed by distinct parameter index/hash reports for the same slot; no absolute normal-Plugin page index is sent. Incident snapshot: control_page_issue_snapshot.json. Temporary receive trace wrapper removed.

Added Plugin-scoped page_targets parameter library, seeded from existing active targets. Hardware learning retains old definitions; arrows clear active slots/watchers and old queued feedback without deleting definitions. CONTROL MAPPED restores the matching target by index/hash. New indices reserve inactive library entries too. PLUGIN entry/reconnect clears old active slots before recall. Offline removals no longer bulk-unmap unrelated page slots after another control confirms. Library is isolated across Tracks and stripped from generic exports. No absolute page counter is guessed.

162 tests pass, including eight pages with 8 knobs plus 8 buttons each (128 definitions), A/B/A, reconnect, Clear isolation and empty-page input gating. Native fixture passed actual parameter writes, two-page recall and tox save/reload retaining off-page targets. Generic .28.tox reload is empty/disconnected with no external DAT references; network layout unchanged and clean. Evidence: control_pages_native_verification.json; native harness: diagnostics/runtime/verify_control_pages.py. Saved roto_control_python.44.toe and promoted canonical project/export. Main connection requested for physical retest. Current preserved T Plugin library contains Mix at index 129; records previously deleted by the old implementation cannot be inferred from unknown hashes and must be re-learned once. Physical control-page acceptance is pending; previous Track acceptance remains separately scoped. No commit/push.


## Physical Plugin control-page regression acceptance (2026-10-07)

User confirmed Page 1 -> Page 2 -> Page 1 works after re-learning Page 1, and also confirmed TD parameter control works. Live inspection on T/CUSTOM showed Sortcrit mapped on Knob 1, with both Mix (index 129) and Sortcrit (index 128) retained in page_targets, no Lasterror or operator errors. Recorded in control_pages_hardware_verification.json. This is physical two-page acceptance; eight pages/128 targets retain automated coverage only. Saved mappings through live TD as roto_control_python.45.toe; canonical project matches, connection retained. Generic export remains empty .28.tox. No runtime changes, commit or push.

## Two Binding workflows and native MIDI retest (2026-10-07)

User chose Parameter mapping plus Python registration. Binding menu now exposes only those workflows (stable internal values collection/callback). Removed seven old single-target configuration parameters; Binding retains mode, collection ID and Apply setup. Public single-target methods remain available in code/hooks. setup.configure_ui migrates an old parameter/value setup through the Layout registry before changing the menu; build/upgrade/export use the same helper. Initial live UI change preserved the complete registry and control snapshots. Fresh builder verified legacy Value migration, callback Apply/reinit/return to parameter mappings and registry preservation. Main reinit retains both Mix/Sortcrit page definitions and the Lowthresh Track. Runtime catalogs naturally update disconnected/connected state during reload; configuration identities are retained.

162 unit tests pass. Live external reconnect recalls Sortcrit without re-LEARN, no errors. Clean reusable .29.tox reload verifies exactly two menu choices, empty target registration, disconnected startup and embedded source/docs. Project saved through live TD as .47.toe; canonical project/export copies promoted. No new physical knob/motor/LCD acceptance is claimed.

Native receive was actually retried in separate input-only TD 2025.33230 processes using a unique virtual CoreMIDI source and independent mido/rtmidi reference. CC-only passes. Two mixed 35-SysEx/three-CC captures each emit 35 unsent three-byte messages, apart from separate normal F7 end-marker rows. One-PING Bytes-On reproduces the native CoreMIDI/libMIDI/OSX_CrashHandler stack before Python callback dispatch. Bytes-Off one-PING remains responsive but emits an unsent extra event; its native DAT table confirms the discrepancy. Both 35-SysEx-only settings lose response, without sampled crash evidence. No ROTO host, output, target binding or physical ports are used. Exact native defect is unconfirmed; production retains the external backend. Runnable probe, evidence and caveats are in diagnostics/native_midi/README.md. All owned diagnostic processes/virtual ports were closed. No commit/push.

## Outer Control page removed (2026-10-07)

User requested removal of the old Control custom-parameter page. Value backing state now lives at base_state.Manualvalue, excluded from public State. The outer Value and Offerparameter parameters are deleted; SetValue/GetValue/Unbind and Offerparameter(id) APIs remain. Shared setup upgrade migrates persisted self-Value destinations without changing IDs or wire identities. Only target watchers dispatch parameter edits; no second internal manual-input observer is added.

164 unit tests pass, including collection registration/removal without outer Control parameters and mirror-echo suppression. Live fresh-builder checks pass old Value migration, SetValue/Unbind, 14-bit built-in value preservation across reload, Python registration reload/return and no Control page. Main Layout configuration matches its pre-upgrade snapshot after synchronizing recall state; Mix/Sortcrit definitions and identities remain. Reconnect recalls Sortcrit without re-LEARN. Generic .30.tox reload is empty/disconnected, has no Control page and embeds updated docs. Four networks/17 groups/63 operators retain clean layout and errors. Saved through live TD as .49.toe; canonical project/export copies promoted. Evidence: control_ui_removal_verification.json. No new physical rotation/motor/LCD acceptance, commit or push.

## Combined Layout custom-parameter page (2026-10-07)

User requested combining Display, Layouts and Tracks, removing permanent confirmation buttons, and clarifying Layout versus Plugin names. Shared setup.combine_context_pages moves parameters into one Layout page with section separators, then removes four obsolete Yes/No parameters. Final outer pages: Connection, Binding, Layout; the Layout page has 11 fields. Active Layout identifies the selected configuration; New / rename Layout is the name draft used by create/rename actions. Hardware Track name and Hardware Plugin name label independent hardware display names, as selected by the user.

Delete Layout/Track now open an asynchronous native popup with Cancel and deletion of the named item. Last-item and LEARN/touch/LOCK guards remain; context changes/reloads expire requests, duplicate callbacks do not delete again. 169 unit tests pass, including popup cancel/confirm, expiry, lock and last-item behavior. Main merge comparison preserved registry/control snapshots and original values/enable states; repeated application is idempotent. Fresh builder and real native popup opening/callback dispatch pass. Clean generic .31.tox reload exposes the three pages, empty assignments and no MIDI process. Embedded docs updated, no new production operators or topology changes. Saved through live TD as .51.toe; canonical copies promoted and external reconnect recalls Sortcrit. Evidence: context_page_verification.json. No commit/push.


## Live Select COMP (2026-10-07)

Implemented optional per-Track Focus COMP links and Binding Follow selected COMP without another mode/page. The three APIs are SetTrackComp, SelectComp and GetCompContext. The current Network Editor's sole selected external COMP resolves only within Active Layout; currentChild is never a fallback. Startup/reload/pane return establishes a baseline, explicit Follow off/on evaluates immediately, and Python registration retains the preference while reporting unavailable. Manual Track selection remains authoritative until a new selection event.

Hardware and TD requests share one guarded arbiter. Selection/unlock fences input, mapping/page recall, FreeLearner commits and feedback immediately, through batch/backlog/partial-line handling. LOCK browsing preserves old-context input until unlock. Recovery requires new matching per-control recall. Both sources carry connection generations and are canceled by Disconnect/Connect/open failure/child failure; fresh disconnected Follow still works. Domain failures retain the transport and do not retry; failed rollback/observer pauses until explicit Apply setup repair.

192 unit tests pass. Native fixture passes current/selected disagreement, zero/mixed/multiple selection, unchanged values/Pulse, idle no-op, same-batch/backlog fences, fresh recall, LOCK/LEARN/touch, stale-session cancellation, offline Follow, repeated upgrade and managed tox reload. Actual stopped-timeline project.save followed by project.load retains renamed Focus links and saved routing with Follow=True, valid restored target, no pending activation and no MIDI process. Native executeDAT introspection exposed projectpresave (omitted from the tool catalog); enabling it is required for onProjectPreSave. Unresolved Focus UI references after rename are resynchronized rather than interpreted as unlink. Fresh builder passes; export reload clears Follow/links/targets/file dependencies, including export before a clone's first Tick. Evidence: comp_follow_native_verification.json; reproducible stages: diagnostics/runtime/verify_comp_follow.py.

Main comparison against live_select_before.json preserves all Layout/Track/Plugin/target IDs, target configuration, Mix/Sortcrit off-page library, Lowthresh Track and original custom parameter values. Both pixelSortV3 Tracks remain unlinked; Follow is off. One new textDAT and Focus annotation add no signal wires. Four networks/18 groups/64 operators pass containment/no overlap/backward-wire checks; controller errors are empty. Source docs embedded. Final artifacts: roto_control_python.55.toe and empty generic exports/roto_python.32.tox; canonical copies match. Main external reconnect is checked separately below. Physical Follow A/B/A, current feedback and guarded switching remain pending; earlier manual Track acceptance is not reused for this feature. Controller-reparent stress and ordinary mouse-click ergonomics retain further acceptance gates. Hardware-to-TD selection and Layout/Plugin name synchronization are deferred. No commit/push.

Main external reconnect after the final save/export passed: T / TRACK / PLUGIN, Knob 1 Lowthresh mapped/valid, Connected/Plugin=True, no Lasterror or operator errors. Main remains connected for testing; saved startup remains disconnected. This is recall verification, not new physical Follow acceptance.

Physical single-COMP Follow test: user confirmed "working" after pixelSortV3 selection activated T / T / CUSTOM and Knob 1 recalled Sortcrit. Live inspection showed mapped/valid Sortcrit=4 (Red), no errors. This accepts the reported selection/knob workflow; LCD was not separately specified. Two-COMP A/B/A, Follow LOCK/unlock and LEARN/touch acceptance remain pending. Test link pixelSortV3 -> Track T and Follow=True remain live; naming is unchanged and the link has not been promoted into the saved canonical project. Evidence: comp_follow_hardware_verification.json.

## Independent Device context / registry v3 (2026-10-07)

User approved proceeding after Ableton/Bitwig/Logic comparison. Track now explicitly groups 1..127 Devices (Plugins); each owns separate identities, current targets and off-page library. Hardware SEL has eight-item Device metadata banks and independent Plugin selection. COMP Follow resolves (Layout, Track, Plugin), with Plugin-owned Focus links. v1/v2 migration preserves existing groups, IDs, wire hashes, target specifications/removal/relearn state and libraries; existing T / TRACK mapping variants were not merged. v2 Track Focus moves to its sole Plugin. Linked Device names follow actual COMP names; Layout names remain independent. Full COMP name stays in the selector, hardware uses at most 12 printable ASCII bytes. RenamePlugin opts into manual naming; SetTrackComp remains an active-Device compatibility wrapper. Added GetPlugins/CreatePlugin/SelectPlugin/RenamePlugin/RemovePlugin/SetPluginComp. Layout custom page has 16 fields in three sections; no new Binding modes or permanent confirmation buttons.

Same-Track Device switches use the existing fenced arbiter, backlog/partial-line epochs, fresh recall and connection-generation cancellation. LOCK blocks automatic TD Follow and hardware Track routing, but explicit hardware Device selection can replace the locked Device within its routing Track after LEARN/touch/backlog guards. Selected Track divergence persists and unlock follows current selection. Activation/rollback/domain/transport failure policies remain. Hardware-to-TD UI selection/reveal, auto-macros and Device bypass/enable remain deferred.

Native rename-before-tox-save found stale saved target paths despite a valid Focus link. Fixed rebasing destinations inside the linked live COMP across active and inactive mapping variants, retaining target IDs/hashes; also updates assignment/library storage. Source upgrade now force-captures current configuration before source replacement. Generic export clears arbitrary root storage backups before rebuilding documented empty state, so older verification snapshots cannot carry user mappings into the reusable tox.

209 unit tests pass, including same-Track A/B/A, ninth-Device banking, invalid indices/capacity, Clear/library isolation, mixed-source arbitration, LOCK exceptions, LEARN/touch/backlog, actual Tick partial-line epochs, reconnect cancellation, rollback failure, duplicate links, rename/rebase and popup expiry on all three IDs. Existing schema tests now assert Device-owned Focus with the same behavior checks. Native TD 2025.33230 fixture passes two-COMP same-Track Follow without value/Pulse writes, actual parameter/Pulse dispatch, fenced old input, fresh recall, locked Device selection, ninth-Device list/select, repeated upgrade, managed tox reload and actual stopped-timeline project.save/project.load with valid renamed target/link/name. TD restarts its global clock on load; reopened fixture checks were explicitly run paused again. Bridge recovered after reload; temporary Textport diagnostics were used to inspect the clock. Evidence: device_context_native_verification.json; harness: diagnostics/runtime/verify_device_context.py.

Main baseline deep comparison preserves IDs, targets, libraries, mapping variants and native values. Fresh external builder, native Active Device custom-parameter callback after watcher initialization, Python registration reconstruction/parameter return and generic export reload pass. Generic export is empty/disconnected, Follow off, no links, user backup mappings, DAT file dependencies or child process; embedded docs match source. Four networks / 18 groups / 64 operators remain clean with no new production topology. Upgrade/export/reconnect evidence: device_context_upgrade_verification.json; baseline: device_context_before.json.

Saved through TD as roto_control_python.57.toe (explicit .56 destination also produced TD's incremented .57); canonical project bytes match .57. Generic exports/roto_python.33.tox is verified and canonical tox bytes match. Authoritative source docs embedded with geometry retained. Main external reconnect passed on original T / TRACK / PLUGIN context: Lowthresh mapped/valid, no re-LEARN requirement, Connected/Plugin true and no errors. Main is connected for testing; saved startup is disconnected. Existing linked T Device now displays pixelSortV3; unlinked TRACK Device keeps its manual PLUGIN name. Follow preference retained. Temporary fixtures and controller verification snapshots removed. Physical multi-Device SEL/LOCK/motor/LCD acceptance remains pending; prior manual Track acceptance is not reused. No commit/push.

## Delayed Free LEARN acknowledgements / Menu Button (2026-10-07)

User reported Knob 2 Lowthresh and Button 1 Mask Image (pixelSortV3.Masksource) missing from T / T / pixelSortV3. Targeted physical trace confirmed Lowthresh offered first, Masksource offered later with the same unreserved index, and mapping reports arriving together only on LEARN exit. Masksource's Button ACK arrived first but was rejected because no selection CC had reached TD and the offer defaulted to knob; Lowthresh's older ACK then had no pending target. Existing Knob 1 Sortcrit, Knob 3 Highthresh and newly learned Knob 4 Mix remained valid.

FreeLearner now retains offers independently by index/hash for 30 seconds, reserves uncommitted indices, reuses a pending parameter's ID/index and accepts out-of-order ACKs. The 128-offer limit rejects new offers without discarding older ones. Existing pending=None invalidation on Layout/Device/page/fence/session resets clears the entire cache. Menu kind is resolved from its ACK even without selection CC; knob value or button Cycle adapters retain the offered hash, persisted with unchanged options in the Device registry. Changed Menu options still reject commit; non-Menu type mismatch remains guarded.

216 unit tests pass. Native actual Parameter Execute edits reproduce newest Mask/Button ACK before older Lowthresh/Knob ACK after LEARN off; both commit without value writes, dispatch succeeds, and extension reload preserves hashes for fresh recall. Evidence: lowthresh_button_learn_trace.json and learn_overlap_native_verification.json; harness: diagnostics/runtime/verify_learn_overlap.py. Main before/after comparison preserves all current IDs/hashes, libraries, contexts and pixelSortV3 values, including the user's new Highthresh/Mix registrations. Temporary method probes and fixtures removed. Four networks/18 groups/64 operators retain containment, no overlap/backward wires and no errors. Updated controls Markdown embedded. Generic .34.tox reload is empty/disconnected, Follow off, no Focus link or MIDI process, with updated code/docs. Saved through TD as roto_control_python.59.toe; canonical project/export promoted. Failed Lowthresh/Mask mappings were never saved by the old code and require new physical LEARN; post-fix physical acceptance is pending. No commit/push.

Post-fix physical acceptance passed: user re-learned Knob 2 Lowthresh and Button 1 Mask Image and confirmed both respond normally. Live checks show both mapped/valid, Masksource mode Cycle; existing Knob 1 Sortcrit, Knob 3 Highthresh and Knob 4 Mix remain mapped. Evidence: learn_overlap_hardware_verification.json. Saved accepted mappings through TD as roto_control_python.61.toe and promoted its bytes to canonical project; generic .34.tox remains unchanged and empty. Saved startup is disconnected; live controller reconnects for continued use.

## Cycle LED / LCD feedback (2026-10-07)

User then reported Button 1 LED always off/immediately cleared and its Menu LCD staying on Source. A deterministic two-choice Menu test reproduced TOGGLE feedback sending zero after advancing to the second choice; PUSH also retained the press latch when software selected the first choice. Cycle shared Pulse's _pulse_state for LED output, despite having a persistent Menu value. Control._feedback now uses selected Menu state for Cycle LED: first option off, other options on. RX press/release state remains separate, and Pulse's established idle/press feedback is retained. No parameter name, COMP or slot is hardcoded; existing IDs/hashes and assignments stay unchanged and require no re-LEARN.

218 unit tests pass, including TOGGLE/PUSH two-choice LED state, software writes, PUSH release, three-choice wrap/nonfirst state and selected-option LCD packets. Live trace shows Button 1 CC feedback and matching option text; the user confirmed LED and LCD both switch normally after this change. No additional display command or label change was needed; TD labels remain Source (Input 1) / Control (Input 2). Evidence: cycle_feedback_before.json and cycle_feedback_hardware_verification.json. Temporary send/receive probes removed. Main five controls retained; network geometry remains four networks/18 groups/64 operators with no overlap/backward wires or errors. Updated controls Markdown embedded. Saved through TD as roto_control_python.63.toe and exported empty generic exports/roto_python.35.tox; canonical copies promoted. Saved startup stays disconnected, live MIDI reconnects for use. No commit/push.

## Tagged COMP discovery / separate Layout and Device pages (2026-10-07)

User chose separate Layout and Device contexts: Layout T stays a mapping set, Track T groups Devices, pixelSortV3 and fractal_pop each own their mappings. Explicit roto_device OP tags register a Device in Active Layout / Active Track during an idle scan, approximately once per second. Existing links anywhere in Active Layout are reused; removing a tag retains saved mappings. Registration respects LEARN/touch/LOCK/routing/transport guards, Track capacity and transactional rollback. Follow handles adding a tag to an already selected COMP, including an existing linked Device, while retaining startup selection baselines. No per-COMP Layout creation or Layout/Device name synchronization.

FreeLearner rejects edits outside the active linked Device's COMP subtree; nested linked Devices own their more specific scope. Discovery and delayed ACK commit apply the same check. Unlinked/manual and Python registration compatibility remain. The outer UI now separates Layout (10 fields) and Device (6 fields), retaining parameter names and APIs. Labels identify Active Layout (mapping set), Active Track group (FUNC), and Active Device (SEL). No new Binding mode, confirmation button or production operator.

228 unit tests pass. Native TD 2025.33230 fixture verifies actual OP tags, Parameter Execute LEARN, foreign-COMP rejection, isolated dispatch/libraries, rename/reload/hash recall and idempotent UI migration (tag_device_native_verification.json; diagnostics/runtime/verify_tag_devices.py). User physically confirmed fractal_pop Knob 1 Power responds and returning to pixelSortV3 restores its original mappings; Layout stays T (tag_device_hardware_verification.json). This accepts tagged-COMP Follow/LEARN/recall, not physical SEL/LOCK/motor/LCD switching.

Main source reload preserves all mapping configuration, identities/libraries and target values, including the newly learned fractal_pop Power. PixelSort's five mappings recall on external reconnect, with no runtime errors. Temporary probes/fixtures removed; four networks/18 groups/64 operators retain clean geometry. Updated authoritative docs embedded. Final live-TD save: roto_control_python.67.toe; generic exports/roto_python.37.tox reload is empty/disconnected, Follow off, no Focus link or MIDI process, and embeds current source/docs. Canonical copies promoted; saved startup is disconnected, live MIDI reconnects for use. Intermediate .65/.36 snapshots precede the final physical-acceptance documentation. No commit/push.

## PR #1 Device metadata index follow-up (2026-10-07)

Followed up the PR's Ableton-comparison comment (issuecomment-6027764498). Regression tests reproduce deleting A from [A, B, C] while B is active, or deleting active A after selecting B as successor: the list becomes [B, C] but host.plugin_index remains 1. remove_plugin now recomputes the active Device index from the final list even while disconnected. Host.set_display_names sends Device details only when the Device name changes, so Track-only rename does not resend Device metadata. Upstream Ableton/Bitwig sources remain unchanged; the reported lack of an explicit Ableton Device-deletion listener remains an unverified observation.

230 unit tests pass, including metadata index after both deletion paths, subsequent Device rename and Track-only rename without identity/library changes. Native TD 2025.33230 isolated clone passes the same cases without physical MIDI I/O (diagnostics/runtime/verify_device_metadata.py; device_metadata_native_verification.json). Fixture removed, main project/mappings untouched. This follow-up changes local source only: live main and canonical .67.toe/.37.tox still contain the prior runtime and have not been upgraded/exported for this fix. No physical acceptance, commit, push or GitHub reply posted.

User requested testing and the fix is now installed in live TD. Re-ran 230 tests and the native deletion/rename fixture. Main reload preserves every target, library, identity, assignment and COMP value; restore hydrates assignment identity/Menu metadata from the unchanged saved targets. Generic .38.tox reload passes empty/disconnected/Follow-off/no-Focus/no-file-dependency checks and embeds current source/docs. Geometry remains four networks/18 groups/64 operators with no errors. Saved through TD as roto_control_python.69.toe, promoted canonical project/export copies and verified their bytes. External reconnect recalls all five pixelSortV3 controls; inactive fractal_pop Power is retained. Evidence: device_metadata_main_before.json and device_metadata_upgrade_verification.json. Live is connected for hardware testing; saved startup is disconnected. Physical deletion/rename LCD acceptance remains unverified. No commit, push or GitHub reply posted.

Physical Device metadata acceptance subsequently passed. In a temporary Metadata test Layout, the user confirmed hardware SEL lists A TEST/B TEST/C TEST and selects B. After deleting preceding A, B RENAMED/C TEST list positions, TRACK NEW display and hardware C/B selection are correct. Deleting active B automatically selects C RENAMED, FINAL TRACK displays correctly, and SEL contains only C with no A/B residue. Software confirms the surviving Device index is 0 in both deletion cases. Evidence: device_metadata_physical_before.json and device_metadata_hardware_verification.json.

Temporary Layout and controller test storage removed; original mapping configuration, IDs, targets and libraries match the baseline (restored assignment metadata is validated against saved targets). Follow preference restored, T / T / pixelSortV3 active, and five original controls recall. Saved cleaned project through TD as roto_control_python.71.toe and promoted canonical copy; generic .38.tox remains unchanged. Saved startup is disconnected, live MIDI reconnects. This accepts the tested unlocked deletion/rename/SEL display cases, not Device LOCK or motor behavior. No commit, push or GitHub reply posted.

## Physical Device LOCK selection (2026-10-07)

In a temporary two-Track LOCK test Layout, the user confirmed LOCK remains on and routing Device stays A DEVICE 1 after FUNC selects LOCK TRACK B. Live inspection confirms routing Track A, selected Track B and no input fence. While still locked, hardware SEL lists A's Devices and successfully selects A DEVICE 2; LOCK and selected Track B remain, with no pending/gated/error state after activation. Unlock automatically activates LOCK TRACK B / B DEVICE 1, with only B DEVICE 1 in SEL. Evidence: device_lock_physical_before.json and device_lock_hardware_verification.json. This accepts these selector/display cases, not mapped-control dispatch or motor behavior under LOCK, ninth-Device banking or TD Follow while locked.

Test Layout/storage removed, Follow restored and original mapping configuration/identities/libraries retained; assignment metadata is validated against unchanged saved targets. T / T / pixelSortV3 restores its five controls. Source Layout docs updated and embedded with geometry preserved. Generic .39.tox reload is empty/disconnected/Follow-off/unlinked and contains current code/docs. Clean project saved through TD as roto_control_python.73.toe; canonical project/export copies promoted. Saved startup disconnected; live MIDI reconnects. No runtime source changes, commit, push or GitHub reply posted.

## Physical mapped controls and motor feedback under LOCK (2026-10-07)

User requested testing the remaining mapped-control/motor case using existing mappings. With pixelSortV3 locked and FUNC selecting TRACK, Knob 2 changes Lowthresh; Button 1 twice changes Mask Image with matching LED/LCD and returns to the original Menu choice. TD inspection verifies Lowthresh input and unchanged fractal_pop Power. Software Lowthresh=0.75 drives Knob 2 to approximately 75% and LCD=0.75, confirmed physically while LOCK stays on. Track intent remains pending under LOCK without an input fence, as designed.

Still locked, hardware SEL switches to fractal_pop; Knob 1 changes Power, LCD identifies Power, and rotating unassigned Knob 2 leaves pixelSortV3 Lowthresh=0.75. Inspection also verifies the old Knob 1 Sortcrit value is untouched. Software Power=12 drives Knob 1 to approximately 71% and matching LCD=12; the user confirms motor/LCD, unchanged Lowthresh and LOCK. Subsequent hardware unlock is observed activating T / TRACK / PLUGIN. Evidence: device_lock_controls_physical_before.json and device_lock_controls_hardware_verification.json. This accepts these existing two-Device mappings, button feedback, motor feedback and cross-Device isolation under LOCK; ninth-Device banking and locked TD Follow remain separate gates.

Restored Lowthresh=0.454312396996887 and Power=8.164682903009217, original T / T / pixelSortV3 context and Follow preference. All original COMP numeric/Menu/Toggle values and mapping configuration/identities/libraries match the pre-test snapshot; added assignment metadata is validated against saved targets. Test storage removed, docs updated/embedded with clean geometry. Generic .40.tox reload is empty/disconnected/Follow-off/unlinked and embeds current source/docs. Saved through TD as roto_control_python.75.toe and promoted canonical project/export copies. Saved startup is disconnected, live MIDI reconnects. No runtime source changes, commit, push or GitHub reply posted.

## Compact Inspector live-data prototype (2026-10-07)

Separate `/inspector_model`, `/inspector_below` and `/inspector_popup` prototypes now project the existing controller data. A shared bounded four-context cache and event-driven DAT/parameter observers coalesce sync at frame end; drafts/scroll/selection remain view-local. Real Layout/Track/Device browsing does not change hardware routing. Active non-Pulse Value edits use SetValue; mapping metadata and inactive Device edits are read-only. Hardware LEARN controls the warm surface/alert. One main Inspector can switch Fold/Popup styles; editors open only on user selection and are left collapsed. Production controller runtime and upstream Ableton/Bitwig source are unchanged.

User physically confirmed K2 value updates and LEARN on/off alerts both work. Native checks additionally pass Value Apply/event refresh, inactive fractal_pop Power updates through a parameter watcher, route-preserving browsing, single-main-window behavior, session/revision guards, and generic tox reload with no controller link or saved destinations. UI export/reload retains the production connected session/catalog. 230 runtime + 21 Inspector model tests pass, with no operator/subscriber errors. Read-only sync probe p95 is 0.395 ms over 100 calls; unchanged snapshots write no text and 1,000 requests retain one scheduled run. This does not establish total rendering performance or long-duration memory stability. Evidence and current limitations: docs/history/inspector/LIVE_REPORT.md and live_*.json.

TD was restarted after the user's request using inspector_restart_checkpoint.1.toe. Initial live-TD checkpoint inspector_real_data.1.toe reloads the real adapter, preserves IDs/context and user values within TD serialization precision (maximum observed float delta 1.72e-7), and starts MIDI disconnected. Live controller was reconnected and only the Fold Inspector is open. Generic inspector_model.tox / inspector_below.tox / inspector_popup.tox embed code and start with no configured controller or user destinations. Canonical roto_control_python.75.toe and exports/roto_python.40.tox were not replaced. No commit/push.

User renamed the displayed BELOW style to FOLD. UI label, presentation menu and window title use Fold; internal component/style identifiers remain below. The latest inspector_real_data.toe save includes this label and an embedded snapshot of the prototype README.

## Compact Inspector Ping / Clear (2026-10-07)

Both Fold and Popup editors now use 24 x 24 icon actions: Ping/Clear top right, Cancel/Apply on the right of the status/Value edits live target row, with hover descriptions. The user's spacing refinement uses 12px side insets, 6px row/control gaps and a 178px editor height without the spare footer space. Ping uses existing Offerparameter and requires hardware LEARN/PLUGIN plus the selected active registration; sending is explicitly awaiting ACK, with no Value/Pulse action. Clear uses RemoveControl, retaining the target Value, after a second inline click within eight seconds. Context/session/revision checks and LEARN/touch guards protect removal. Mapping metadata stays read-only; inactive browsing cannot mutate controls.

230 runtime + 33 Inspector model/editor tests pass. A disconnected native clone verifies forgotten-map metadata output, LEARN guard, Pulse isolation, Clear confirmation and single-registration removal without production catalog/registry/session changes. Geometry and operator errors pass. Physical Ping/re-LEARN acceptance is pending. Source builders and generic UI exports include the new controls; latest project checkpoint is inspector_editor_actions.2.toe, preserving the user's Popup preference with one main Inspector and no open editors. See prototypes/inspector/editor_actions_verification.json. No production runtime edits, commit or push.


## Compact Inspector health / shared commands (2026-10-08)

Milestone 1 of docs/history/inspector/BUILD_PLAN.md is installed: row health markers and editor state, one shared command/capability module, four-context scalar native-definition cache, exact touch/mode observers and callback-node cleanup for Fold/Popup. Saved inactive/disconnected targets never claim a current ACK. Invalid inactive targets are resolved independently so one bad target cannot interrupt the remaining UI. Touch/LEARN updates change action availability without expiring Value drafts; native definition changes invalidate them. Existing controller APIs remain authoritative and original mappings/session are preserved.

230 runtime + 42 Inspector tests pass. Disconnected native fixtures pass health/guards, six-context cache bounds and native touch/same-Value EXPRESSION mode callbacks without manual refresh. Idle causes zero extra text writes; 1,000 requests retain one scheduled run. Matched two-context projection/dispatch p95 is 0.223ms before / 0.177ms after; excludes native rendering/MIDI/full frame cost and long-duration memory acceptance. Generic UI export/reload verifies embedded promoted commands, empty definition cache, no controller/destinations and two subscriptions. Root groups have measured containment/gaps and no functional overlap/errors.

Saved through live TD as inspector_editor_actions.3.toe; generic Inspector tox exports updated. One main Inspector retains Popup presentation with no open editor. Canonical production project/runtime and upstream integrations are unchanged. Milestones 2–6, including mapping configuration and native parameter definition work, remain planned; the old Inspector remains necessary. Physical forgotten-map Ping/re-LEARN is pending. Evidence: docs/history/inspector/HEALTH_REPORT.md and health_*.json. No commit/push.


## Compact Inspector Mapping / dropdowns / live Value (2026-10-08)

Milestone 2 is installed: Device occupies the first header row, Layout | Track share the second, all using native TD dropdowns. Direct mouse selection browses inactive fractal_pop without changing hardware routing. Mapping opens one reusable section with its own draft/token and 24px Apply/Cancel; Range, compatible Mode and input adapter use one guarded ConfigureControl call. Range/Mode semantics require re-LEARN; input-only PUSH/TOGGLE retains ACK. Native Menu/Toggle/Pulse and Python registration callback cases are verified separately.

Value is now a continuous live edit with no visible Value Apply/Cancel. Only user text callbacks dispatch SetValue; model updates refresh the unfocused field without echo writes. Finite/range/stale/context/LEARN/touch guards remain. Native callbacks and a deferred-frame check verify direct writes, deduplication and no model echo in a disconnected fixture. Production mappings/catalog/registry/session are preserved.

Popup Size from Window fixes native aspect-locked resizing: real mouse width-only and height-only drags leave the other axis unchanged. Popup owns its own dimensions; selecting controls does not resize it to the Inspector. Opening Mapping changes content height only (178 -> 312), retaining native window size and scrolling. Fold expands inside the scrolling list. Source builders, grouped networks and generic UI tox reload pass; exported Mapping draft/controller/destinations are empty with two subscriptions. 230 runtime + 61 Inspector tests pass, no operator/subscriber errors or frame polling. Accordion reuse retains node counts; model-only p95 is approximately 0.190ms, excluding rendering/full frame cost.

Latest live-TD save: inspector_editor_actions.4.toe. One main Inspector, Popup preference, no open editor. Canonical production project/runtime and upstream integrations remain unchanged. Target picker/typed widgets and further parity remain later milestones; old Inspector still required. Physical Range/input re-LEARN and forgotten-map Ping remain pending. See docs/history/inspector/MAPPING_REPORT.md and mapping/live_value/dropdown/window_sizes verification artifacts. No commit/push.


## Popup accordion height and native icons (2026-10-08)

User’s two screenshots clarify that expanded Mapping grows the Popup downward, independently of free width/height resize. UI now adds/removes only 134px from the current manual height, preserving width/top-left/upper fields and main Inspector. OS-close/pending-size and extension-disconnect restoration prevent accumulated section height. Reopen reads viewport content dimensions because TD’s closed window cache can include the 32px title bar after reload; native reopening retains 334x318. Four editor actions and inline Clear confirmation use TD’s bundled Material Design Icons font. Value remains continuous live edit with no Cancel/Apply. 230 runtime + 68 Inspector tests and staged native window geometry fixture pass. Latest checkpoint: inspector_editor_actions.6.toe; generic UI exports contain embedded source and no user mappings/drafts.

Actual horizontal native mouse resize reproduced a persistent white bottom strip. Root-display toggle and forced viewport/window cook did not fix it; probes were reverted. TD’s direct panel capture renders the full dark surface correctly. Native UI automation subsequently timed out, so native repaint/flicker root cause and fix remain unresolved. No polling/per-frame render or speculative resize workaround added. One main Inspector, no extra editor; production mappings/session remain intact. No commit/push.


## Trim Inspector editor spare height (2026-10-08)

User reported unused empty space. Existing Popup native content was 334x318 with a 178px editor. External fit_editor_height.py trims it once to 334x178, preserving width/top-left/main Inspector. Native expand/collapse passes 334x178 -> 334x312 -> 334x178 with viewport matching editor content and unchanged production catalog. Manual resizing remains free. No runtime source/topology changes or new tests; existing 230 runtime/68 Inspector results remain the last test baseline. Updated generic exports and checkpoint inspector_editor_actions.7.toe through live TD. Prior native repaint issue remains unresolved. No commit/push.


## Ping icon meaning (2026-10-08)

User found the refresh-arrow Ping icon misleading. Changed Ping to the bundled Material Design Icons access-point glyph (F0003), showing outward signal waves; Clear/Mapping actions retain the same icon font. All four existing editor hosts updated, no additional window/operator or command behavior change. Compact 178/312 heights retained. Embedded source/generic exports updated; checkpoint inspector_editor_actions.8.toe. No commit/push.


## Native resize deformation deferred (2026-10-08)

User confirmed that main Inspector and Popup resizing deforms text/icons and stretches/moves fields. The independent Popup panel-root and native-anchor trial applied live after `inspector_editor_actions.8.toe` did not resolve the reported behavior. No visual fix or renderer root cause is established. These latest live UI changes are not yet a new saved/exported checkpoint. Existing geometry/pure-test results do not prove native drag rendering. The temporary frame probe was removed; `resize_frame_profile.json` captured 1,200 idle samples and zero resize frames, so resize cost remains unmeasured.

At the user's request, published [issue #6](https://github.com/joshuahhn/roto_control/issues/6) with `bug` and `ready-for-agent`, including reproduction, attempted mitigations and native-window acceptance criteria. Stop investigating resize for now and continue with Milestone 3 target picker/typed Value controls. The issue remains open; old Inspector replacement acceptance remains incomplete. README and build/report notes now reflect the unresolved status. No new live TD changes, binary save/export, commit or push in this issue-recording step.


## Compact Inspector target picker / typed Value (2026-10-08)

Milestone 3 is implemented in both Fold and Popup: click Target to open a searchable COMP-scoped picker with six reused rows, explicit Assign/Cancel and paging/Refresh. Empty-slot assignment and retargeting use the existing controller authority; search/select/cancel do not write mappings or Value. Shared scalar discovery has 32 snapshots/4,096 total entries, finite traversal/work bounds, at most two jobs and one pending continuation each, with a cooperative 2ms slice budget. Candidate native/bind-chain definitions are revalidated before Assign. Context/session/target/touch guards, duplicate ownership and old-registration fencing preserve other controls. HW LEARN assignment offers once and reports awaiting ACK without claiming hardware success.

Value uses live Float/integer fields, a checked native Menu dropdown with indexed labels, or ON/OFF Toggle; no Value Apply/Cancel. Changed Menu definitions reject stale callbacks. Pulse stays read-only. Picker/Mapping are mutually exclusive, collapsed content remains 178px, Mapping 312px, picker 428px, with existing Popup downward height delta and Fold scrolling. Hidden result/widget labels and scope/query are scrubbed from generic exports. No extra editor windows, per-frame tree scan or production runtime edits.

230 runtime and 79 Inspector tests pass. Native fixtures, fresh view builder, Mapping/live Value regressions, grouped-network containment/overlap checks and generic source/export reload pass. Production catalog/registry/session remain intact, with two subscribers and no prototype errors. Actual-project discovery slice p95/max 2.064/2.120ms, cached open 0.0107ms, query plus UI 0.249ms and idle sync 0.141ms; no query rescan, node growth in 20 reopen cycles or idle text-write growth. Native rendering/MIDI and long-duration memory are not measured. Physical new assignment/LEARN remains pending. See docs/history/inspector/TARGET_REPORT.md and targets_*.json.

Checkpoint: inspector_editor_actions.10.toe, saved through live TD with generic Inspector tox exports refreshed. One main Inspector retains Popup preference, with no open editor. The independent Popup root/native-anchor trial is now included but still does not resolve native resize deformation; issue #6 remains deferred. Old Inspector replacement and milestones 4–6 remain incomplete. No commit/push.


## Value Float / Int cycle and physical assignment / Ping acceptance (2026-10-08)

User requested choosing Float or Int for numeric Value, then specified a cycle action. Both editor presentations now have a compact 48px Float ↔ / Int ↔ button on the existing Value row. The choice is local to the selected editor and defaults to native Style on a different slot. Switching preserves target Value, Style, mapping Range and re-LEARN state; it sends no Value write, including after deferred callbacks. Int input accepts whole numbers; a native Int target still rejects fractional input in Float mode. Menu/Toggle/Pulse keep their appropriate controls. Collapsed/section heights and window count remain unchanged.

Native fixtures pass actual cycle callbacks, integer input for Float, fractional rejection for native Int in Float mode and no deferred writes. 230 runtime / 79 Inspector tests and generic exports pass. User also confirms physical target assignment and Ping working; evidence records the user statement and a read-only current-controller snapshot in prototypes/inspector/targets_hardware_acceptance.json. Range/input-adapter, long-duration stress and full replacement remain separate gates. Latest checkpoint: inspector_editor_actions.11.toe, with updated embedded README and generic exports. No commit/push.


## Serial and binding architecture issues / HW Type label (2026-10-08)

Published user-requested issues [#7](https://github.com/joshuahhn/roto_control/issues/7) for optional read-only Serial API integration/transport feasibility and [#8](https://github.com/joshuahhn/roto_control/issues/8) for CHOP/binding-driven value ownership, Roto takeover, configurable inactivity return and direct-Python/reference-expression/native-BIND sync strategies. Both are enhancement/ready-for-agent investigations with public-seam tests, native/physical acceptance and lifecycle/performance gates. #8 coordinates with BIND ownership conflict issue #5; source authority and sync mechanism are separate, and arbitrary existing expressions/exports must not be silently overwritten. No serial or new binding runtime is implemented in this issue-recording step.

Renamed the Mapping field label Input to HW Type in all four existing editor hosts and the external builder. It remains a declared PUSH/TOGGLE RX adapter; this label does not claim hardware auto-detection or configuration writes. Internal parameter/API names and behavior are preserved. Source docs and embedded README/generic exports refreshed; saved through live TD as inspector_editor_actions.15.toe. No new operators/editor windows, runtime behavior change, commit or push.


## Popup section opening avoids reopen (2026-10-08)

User reported a close/reopen-like flash when clicking Target or Mapping. Native probe confirms `winh` updates an open window without `winopen`; section expansion redundantly pulsed Open afterward. Removed only that pulse, preserving automatic downward height deltas, independent manual size and top-left position. Regression test fails on the former four Open pulses and passes with zero. Staged native Mapping/Target/Mapping/collapse verifies 134/250/134/0 deltas, unchanged width/top-left/main size, zero Open/Close pulses and unchanged production catalog/session. Native geometry settles after window processing; allow at least two frames between fixture stages. Probe DAT/storage removed.

230 runtime / 80 Inspector tests pass; generic exports refreshed. Saved checkpoint inspector_editor_actions.13.toe. User visual flash acceptance remains pending; this fix does not claim resolution of manual resize deformation in issue #6. No commit/push.


## Section resize keeps the current native width (2026-10-08)

User confirms Target/Mapping no longer flash, but width changes in between when pressed. Opening Width can remain stale after native manual resizing; offset changes before width synchronization temporarily apply that stale width. The regression records a 376px manually resized window snapping to 286px under the old ordering, then remaining 376px under the fix. Capture native x/y first, synchronize opening width only if stale, then update vertical offset/height. No Open/Close/Update Settings pulse, polling or native OS bridge is introduced. An Update Settings probe included title-bar height; temporary dimensions were restored and the probe state removed.

230 runtime / 81 Inspector tests and staged native geometry/no-reopen checks pass. Flash disappearance is user-accepted; intermediate-width visual acceptance remains pending. Source Markdown/embedded README/generic exports updated, checkpoint inspector_editor_actions.16.toe. Issue #6 remains deferred. No commit/push.


## Section flash and width physical acceptance (2026-10-08)

User confirms the intermediate-width problem is fixed, following confirmation that section-opening flash is gone. Target/Mapping section transitions are now user-accepted for both reported symptoms. Recorded separately from agent geometry/pulse checks in prototypes/inspector/popup_no_reopen_verification.json. Manual window-resize deformation remains deferred in issue #6. Acceptance-record update only; no runtime changes, project save, commit or push.

## Compact Inspector milestone 4 (2026-10-08)

User accepted the section-toggle width fix, then requested the next milestone. Native resize deformation in issue #6 remains deferred.

Added view-local COMP/callback filters, a compact native-icon Details section, stable target IDs/errors, separate view/controller Follow state, LOCK and selected/routing/gate diagnostics. RX/TX/rejected are sampled on open/Refresh. Reveal uses the existing Network Editor with controller Follow OFF; Repair reuses the existing Target picker and still requires explicit Assign.

Clear Device confirms full Layout / Track / Device and all current active registrations, including filtered-out rows. It delegates the existing RemoveAllControls scope, preserving other Devices, target Values and inactive hardware-page libraries. Eight-second single-use confirmation revalidates scope/session/registration/native definitions; LEARN/touch/inactive browsing are blocked. Partial failure reports removed/remaining counts and error.

230 runtime / 87 Inspector tests and isolated native parameter/callback fixtures pass. Production catalog/registry/routing/MIDI session are preserved. Fresh builder no longer rewrites identical parity source (avoiding shared-model reload); two subscriptions remain. Bounded Python measurements: idle sync p95 0.255ms, Details Refresh 0.281ms, Fold close/open pair 0.967ms; operator count stays stable. These do not measure OS rendering, transport or a long-duration soak. See docs/history/inspector/PARITY_REPORT.md and parity_verification.json / parity_performance.json.

Generic Inspector exports and embedded README are refreshed through live TD; active project saved as a checkpoint with one main Inspector, Popup preference and no open editor. Next slice is Milestone 5 replacement acceptance, including matched render/soak and physical configuration re-LEARN gates. Old Inspector remains available. No production runtime changes, commit or push.

## Info hierarchy and physical tab recognition probe (2026-10-08)

User reports intermittent two-click header selectors, difficult uniform Info text, and different hardware FUNC/SEL layouts. They clarified Function means the physical Roto FUNC screen and requested a test file before deciding the Custom Device/registry approach.

Info now uses bold group headings (Mapping / Hardware routing / Technical), muted labels and larger main values. Long path/ID/context fields occupy full-width rows in a scrollable Technical group, with an explicit native wheel callback. Equal detail signatures skip field/layout writes. Native parity/scroll/reopen checks and generic scrubbing pass; the existing section/window footprint is retained.

Thirty native virtual clicks open Device/Layout/Track once each, including switches with a previous menu open. This does not reproduce the intermittent physical click symptom or prove macOS click delivery. Do not claim that bug fixed. A temporary recorder in prototypes/inspector/tab_layout_probe.py captures physical General/Track, Plugin/Device, MIX and normal page messages plus menu click/open/focus/close events. It forwards existing handlers without synthetic sends, routing/Value/mapping changes, new ports or polling. Bounded to 512 events; disk writes only on Save/Mark/Stop. Native start/stop smoke restores hooks and preserves production context/catalog/session. See TAB_LAYOUT_TEST.md and selector_click_verification.json.

230 runtime / 92 Inspector tests pass. Before physical capture, generic exports and embedded README are refreshed and checkpoint saved through live TD. Recorder is temporary, not embedded/exported; stop/save it before extension reload or TD restart. Current physical capture lives in the active controller extension's _tab_layout_probe, if present; source Mark/Save/Stop can access it from a freshly executed namespace. User must report actual FUNC/SEL screen names because packets do not prove visible screen state. Registry hierarchy remains Layout -> Track -> Device; special Custom Device and hierarchy changes await this evidence. No commit/push.


## Physical tab findings and menu-item clarification (2026-10-08)

Physical FUNC shows T / TRACK, held SEL shows pixelSortV3 / fractal_pop, released LCD shows pixelSortV3 / T. These match Track and Device lists. LCD T is Track; TD Layout also happens to be T. Inspector selectors browse only, and captured Custom browsing did not change active T / T / pixelSortV3 routing. tab_layout_capture.json saved/stopped: 59 events, zero drops/errors/conflicts, original hooks restored. No Custom Device or registry migration is justified by these observations alone.

The user explicitly clarified that menus open, but **selecting an item inside all three menus sometimes takes two clicks**. Earlier header-opening fixtures addressed the wrong step. The temporary header-release trial was withdrawn on disk/live and its throwaway fixture removed. Thirty staged native list mouse-down/release selections pass; single-call virtual clicks do not deliver equivalent list events and must not be mistaken for a physical repro. No selection fix or root cause is established. verify_selector_items.py and selector_item_verification.json preserve routing/session; recorder source now additionally captures native list gestures/click classification/double-click dispatch and SelectContextMenu return acceptance. Temporary hooks must be stopped/saved before rebuilding or reinitializing. Final physical menu-item capture, if active, is selector_item_capture.json in _tab_layout_probe; use source Save/Stop in an isolated namespace.

230 runtime / 93 Inspector tests pass. Generic exports retain original press header callbacks; no new editor windows or production runtime changes. Checkpoint after export/reload is saved through live TD as inspector_editor_actions.19.toe. After saving, the temporary physical recorder was started at selector_item_capture.json; it is not embedded in that checkpoint. Native resize issue #6 remains deferred. No commit/push.


## Menu-item native event-order trace (2026-10-08)

User physically reproduced first item click ignored, menu remains open. selector_item_capture.json saved/stopped: 50 events, zero drops/errors/conflicts. First Device/Layout gesture has release endrow=-1 then a new press in the same frame; Track also receives an end before start. No first-item selection callback, DoubleClick or LostFocus occurs; later callbacks are accepted. This identifies native event ordering as the failing boundary, not a rejected Inspector callback. macOS/focus cause remains an inference. The finite replay_selector_item_capture.py reproduces zero accepted callbacks first, one on the subsequent gesture while preserving routing/session; it is a callback-seam replay, not an OS-input regression proof.

Targeted trial now uses header release inside + one deferred TD frame, guarded against close/destruction/context/model/session/menu generation changes and duplicate queued releases. This differs from the earlier withdrawn synchronous release trial. Existing header DATs only; no extension/window rebuild or native resource changes. context_callbacks.py generates fresh builder/export callbacks. Pure cancellation/duplicate checks and native held/release/drag-out + 30 staged item selections pass. Physical fix acceptance remains pending; do not claim fixed from software tests. New temporary recorder, if active, writes selector_item_release_capture.json and must be stopped/saved before any rebuild/reload. Runtime stays connected with one main and no editors. Resize issue #6 remains deferred; no commit/push.

Final trial checks: 230 runtime / 98 Inspector tests, 30 staged header+item selections, 30 header openings, held/release/drag-out cases and generic export/reload pass; prototypes have zero errors, two subscribers, no discovery jobs. The native item fixture uses fully staged header and item gestures; coalesced virtual header clicks occasionally delivered no list gesture after the extra deferred frame and are not an OS-input repro. Physical mouse acceptance remains the remaining gate.

Saved trial checkpoint through live TD: inspector_editor_actions.20.toe (verified exists). After saving, selector_item_release_capture.json recorder started; it remains temporary and outside the saved checkpoint. Save/Stop before rebuilding.


## In-window header dropdowns (2026-10-08)

Physical release-plus-one-frame trial failed: first item click still ignored, menu remains open. selector_item_release_capture.json stopped/saved (188 events, zero drops/errors/conflicts); repeated release-before-press remains after menu reopening, actual selection callbacks accepted. The user explicitly requests dropdowns inside the Inspector window. Timing timer removed; no OS/root-cause fix claimed.

Implemented container_context_menu inside each existing Inspector root: fixed 24px native rows, 11px text, MDI checks/arrows, at most eight reused rows. Overlay below the anchored header uses actual button.y, fits rows/footer to available space, and never changes main Window dimensions or opens resource popMenu for these three selectors. Small lists have no unused footer; longer lists support wheel/paging/count. Click outside, scoped ESC, focus loss, other actions, context changes, view switching and Disconnect dismiss. Readonly Text callbacks removed from new labels. Header release-inside opens synchronously; no queued timer. Existing ID/context/session-generation/stale guards remain, browsing never routes hardware.

230 runtime / 98 Inspector tests pass. Native 30 item clicks, header held/release/drag-out, dismissal, same root/no new menu Window, 17-item paging/wheel callback, stale selection/Disconnect, unchanged dimensions/operator count/catalog/routing/session pass. interactMouse wheel did not emit a native wheel event in this TD build; fixture instead verifies the native Panel Execute boundary, so physical wheel acceptance stays pending. Fresh isolated builder passes with same shared model; probe removed and two subscriptions retained. Context network cleanup verifies no overlap/containment. Generic export/reload clears menu fields/checks/keyboard FIFO and retains original production session. Physical first-click and Escape acceptance remain pending. Temporary recorder, if active, is inline_selector_capture.json; Stop/Save before rebuild/reload. No commit/push; resize issue #6 deferred.

Saved final in-window checkpoint through live TD: inspector_editor_actions.21.toe, verified exists. One main open, no Popup editor, dropdown initially closed. After save, inline_selector_capture.json temporary recorder started for physical first-click acceptance; it is outside the saved project and must be stopped/saved before rebuild/reload.


## In-window dropdown physical acceptance (2026-10-08)

User confirms all three menus select items with one click. inline_selector_capture.json stopped/saved: 24 events, five item presses and five accepted callbacks, Device/Layout/Track all observed, hardware routing stable, zero drops/logging errors/restoration conflicts. inline_selector_acceptance.json separates this acceptance from physical wheel/OS Escape, which remain unverified. All diagnostic hooks removed; controller connected, two model subscribers. First-item-click bug and same-window header layout accepted. Native resize issue #6 remains deferred; no commit/push.

Acceptance documentation embedded and generic exports refreshed. Verified saved checkpoint: inspector_editor_actions.22.toe. Recorder is stopped; continue from this checkpoint.


## 2026-10-08 - Editor dropdowns inside Fold and Popup

User prefers the accepted in-window header dropdowns and requested the same approach in the editor. Value Menu, Mapping Mode and HW Type now reuse the pure Dropdown renderer and first-press row callbacks in their existing editor hosts; openers use release-inside without a timer. Numeric Float/Int remains a cycle; Target picker remains inline. Each view has three fixed eight-row pools, only one active, with above/below placement and bounded paging. Dropdown opening never changes Window dimensions or pulses Open. Main/Fold and Popup dismissal/focus are scoped to their actual Window roots (a nested Fold panelRoot alone does not identify its containing Window).

230 runtime / 106 Inspector tests pass. Native disconnected callback/Menu fixture tests both Fold and Popup: first release opens, first row press selects, live Value dispatch, draft-only Mode/HW Type, preserved geometry/open count, no TDResources floating menu, zero errors and two restored subscribers. Production catalog, registry, session and routing are unchanged. Fixture removed; fresh builder creates all pools with no new open Windows. Generic export/reload checks include empty editor pools, keyboard buffers and embedded callbacks. Source README embedded before export. Physical editor first-click acceptance remains to be checked by user; header first-click acceptance is already confirmed. Resize issue #6 remains deferred. No commit/push.

Saved and verified live checkpoint: `inspector_editor_actions.23.toe`. Generic exports reloaded successfully with empty editor pools and embedded sources. Header paging/dismissal regression checks pass after allowing one native focus-update frame before testing Escape. One main Inspector is open in Popup presentation, editor/dropdowns closed, controller connected, two subscribers, no recorder or fixture left running.


## 2026-10-08 - Downward editor dropdowns and excess-height cleanup

User finds upward dropdowns odd and accepts a longer editor, then reports the editor is too long. Editor menus now always open downward. A pure bounded space calculation adds only missing height for at most four visible rows (four visible Menu choices plus paging: 92px extra, 178 -> 270). Controls keep their top-relative positions. Mapping/Picker/Details shift with temporary space. Popup consumes existing free native height first, otherwise expands down with width/top-left retained and no Open pulse. Selection, outside click, Escape, focus loss and Disconnect remove the temporary height; Fold uses its existing scrolling content without enlarging the main Window. Header dropdowns are unchanged.

Observed Popup retained 551px while collapsed editor content used 178px. Applied one-time content fit to both saved Popup hosts, preserving widths 328/240. Updated fit_editor_height.py to close a dropdown first, synchronize actual width before offsets and remove its old Open pulse. Subsequent manual resizing remains free; issue #6 is still deferred. Real K1 snapshot verifies 328x270 with four visible downward rows and paging; collapsed baseline is 328x178. Production Value was not changed by this visual check.

230 runtime / 109 Inspector tests pass. Staged disconnected native fixtures verify both presentations: downward fit, first item selection, temporary editor growth/restored heights, stable Window width/top-left/open count, live Value versus Mapping draft isolation, unchanged production catalog/registry/session/routing, no errors, two restored subscribers. Generic exports and embedded README refreshed. No commit/push.

User clarified that a dropdown does NOT need to display every option at once. Editor capacity is therefore four visible rows; the fixed eight-row pool remains bounded and only four rows are displayed. Remaining items are reachable through wheel/paging/count. Native fixtures verify the last option is reachable and returning to the first page still selects correctly. Header capacity remains eight.

A same-frame menu close/window close could save the expanded Size From Window height, even with Opening Height already collapsed. Generic export now explicitly normalizes the closed host and Opening Height to 178px; reload verification asserts both plus zero temporary menu space. Checkpoint .24 was an intermediate full-eight-row trial; use the subsequent saved checkpoint.

Final clarification: show all options when the existing height can fit them; otherwise use compact paging. Editor capacity is now adaptive: up to eight pooled rows when existing Popup/viewport free height fits, otherwise up to four. The native fixture includes a 342px Popup: all eight rows visible with no footer/no Window growth, then restores the compact baseline. Compact Fold/Popup tests still verify four rows, all remaining options reachable, and 178 -> 270 -> 178 for a base Menu editor.

Final checkpoint saved through live TD: `inspector_editor_actions.26.toe`, verified exists (TD incremented the explicit .25 save). Real K1 review: 328x270 with four visible rows/count, then 328x178 after dismissal; save refreshed after native geometry settled. One main Inspector and compact K1 Popup are open, dropdown closed; production connected, two subscribers, no recorder/fixture.


## 2026-10-08 - Replacement probe interrupted; Popup height accumulation fixed

Following next, M5 finite acceptance runners were added on disk: acceptance_metrics.py, acceptance_probe.py and external sample_process_memory.py. Mapping/target/parity native fixtures pass; 230 runtime / 114 Inspector tests pass. Twenty real-data matched frame cases completed. The 1800-second disconnected sixteen-slot soak was stopped at 352 seconds following the user's oversized Popup report; replacement_acceptance.json is explicitly incomplete. Production catalog/registry/routing/session preserved, clone/probe destroyed, RSS sampler stopped. Source report: REPLACEMENT_REPORT.md. User explicitly reports physical Range / Apply / re-LEARN not yet tested; replacement_physical_gates.json records it. Old Inspector retained.

Observed Popup 2074px versus 178px collapsed content. Reproduced exact growth with settled Mapping -> collapse + close/reopen in same tick: native heights 312,446,580,714,848 instead of178. The Window member could update synchronously while Size From Window still held the expanded cache. ui.py now tracks latest intended geometry across async native/viewport settlement; reopen and dropdown free-space decisions prioritize it. One cancellable three-frame run clears the intent and synchronizes a closed host; Disconnect/export cancel it. No extra Window or permanent frame observer. Manual post-settlement dimensions still supply the new base and keep width/top-left.

Native after replay passes20 reopen cycles at178px; fast section/dropdown replay passes30 cycles; manual376x220 ->376x354 ->376x220 plus original-rectangle restoration passes. Deferred-geometry tests cover same-tick deltas and close/reopen. Editor dropdown gestures still pass. Height guards added to the soak runner to reject drift early. Complete30-minute soak remains pending rather than reclassified as pass. Native resize deformation issue6 remains separate/deferred. No commit/push.

The finite harness now also saves/restores each pre-test Popup rectangle and normalizes only its fixture phase to178px. Short smoke captures use a separate artifact prefix so they cannot overwrite the incomplete30-minute result. Dropdown free-space decisions use the current intended viewport height during settlement, avoiding clipping against a stale expanded cache.

Final fixed checkpoint saved/verified through live TD: inspector_editor_actions.27.toe. Generic export/reload passes with empty geometry state/no pending settlement run. Final real K1 Popup328x178; production controller connected, two subscriptions, no acceptance probe/fixture/RSS sampler. Separate popup_height_fix_smoke_acceptance.json completed a10-second fixture phase after shortened matched cases with no errors and production preserved; it is explicitly not the30-minute gate. Complete30-minute replacement acceptance remains pending.

### Completed height-guarded soak (2026-10-08)

Continued the full finite acceptance run after the height fix: 1800.01 seconds, 16,437 batches of fourteen non-Pulse updates, alternating Fold/Popup and editor sections, no errors or height drift. Operator/subscriber/cache/queue counts stay bounded; production catalog/registry/routing/session preserved. Probe/fixture removed, external RSS sampler exited, real K1 Popup328x178 at(272,312) restored with no pending geometry callback. Interrupted captures archived with `_interrupted`; current full captures and derived summary are replacement_acceptance.json, replacement_rss.jsonl and replacement_summary.json.

RSS after two soak minutes3452.94–3454.28MiB, first/last3453.31/3453.41; last ten minutes3453.16–3453.41. Whole-project matched frame p956.67–8.82ms, closed baselines7.97/8.14. Synthetic minute frame p9515.25–19.46ms and wall-gap p9528.70–31.57ms; explicit Sync+Flush p950.665–0.782ms. Stability passes, but performance headroom needs isolated callback/native-render profiling before acceptance. Bucket case labels represent boundary state and cannot attribute minute cost by style. Fresh builder passes with current source, bounded pools and no test windows.230runtime/114Inspector tests pass. Old Inspector retained; full project restart, physical Range/re-LEARN/input acceptance and deferred resize6 remain open. No commit/push.

### Physical Range ACK status fix (2026-10-08)

User confirmed K2 temporary Range endpoints0.25/0.75, but reported a persistent Needs re-LEARN prompt. Native state shows mapped=True, requires_relearn=False and an empty needs_relearn set: hardware ACK succeeded. Reproduced stale Apply-time Mapping text and ACK-only token invalidation; fixed Inspector display-health projection and dynamic Mapping status, preserving structural/session guards.116 Inspector /230 runtime tests pass; verify_mapping.py covers native publication, both editor roots, retained Value editability and unchanged fixture values. Live sources refreshed with production catalog/session preserved. Original K2 bounds0–1 restored via Mapping Apply; final physical re-LEARN and updated-message acceptance pending. Durable record physical_range_relearn.json; gate restoration_pending. No project save with temporary Range; no commit/push.

Native hardware ACK for restored0–1 Range subsequently received: mapped=True, requires_relearn=False, Mapping status hardware acknowledged in both editor roots, token current. Gate restoration_ack_received; waiting for user restored0/1 endpoint/message confirmation. Generic sources refreshed/exported and reload checked while retaining the production MIDI session.

Physical Range gate now accepted: user confirms restored0/1 endpoints and hardware acknowledged message after the fixed UI. Original live Value0.3430385155343954 restored via SetValue; runtime mapped=True, requires_relearn=False, current editor token and Value editability verified. Gate accepted and physical_range_relearn.json complete.116 Inspector /230 runtime checks and native mapping/export reload pass. Remaining replacement gates: isolated performance headroom, full project restart, declared button adapter and deferred native resize6. No commit/push.

### Callback/publication performance follow-up (2026-10-08)

Active baseline29 verified, then finite matched closed/Fold/Popup/frozen/1-value/14-value fixture workloads in forward/reverse order. Original closed/frozen bursts retain cadence spikes, with old Inspector JSON/table projection consuming most callback time. Cache-only does not solve different intermediate states. Implemented one transient projection signature, bounded owned end-frame optional UI render, early pending guard, cached catalog lazy fallback; authoritative catalog/control outputs/MIDI/Value/Pulse/ACK remain synchronous. No whole-publication coalescing shipped.236 runtime/116 Inspector tests pass with retries/scope invalidation/forced refresh/latest snapshot/cancel/stale owner guards.

Final median per-case frame p95 Fold17.55→7.99ms, Popup15.86→9.57ms, Details17.27→8.38ms; wall-gap p95 still23–24ms, so fixed cadence is open. Full artifacts callback_cost*_timings.json / corresponding acceptance files, derived performance_summary.json, report PERFORMANCE_REPORT.md. All completed probes preserve production and remove operators/wrappers; fixtures never open MIDI. Failed fixture reinit was cleaned up and real data restored before the final run. Main30-minute acceptance capture remains unchanged; replacement_progress.json was explicitly reconstructed from that acceptance after an initial harness prefix mixup.

Live runtime two DAT sources upgraded via install_projection_cache.py, reconnecting existing MIDI; binding identities/Ranges/Values unchanged, six original mappings re-ACKed, no idle projection callback. projection_install.json records before/after. Generic controller exports/roto_python.41.tox reloads disconnected, empty catalog/current embedded sources/no pending callback, production process/catalog preserved during export. Real K2 Mapping Popup328x312 retained. No new30-minute soak or full project restart claim. No commit/push.

### Full process restart and persistent section offset (2026-10-08)

Checkpoint30 actual restart exposed saved Mapping312px reopening as the base, then growing to446px. ui.py now stores only inspector_popup_expansion and removes the saved delta during startup; manual base preserved.118 Inspector /236 runtime checks pass, generic exports reload with offset0 and unchanged production. Fixed checkpoint31 full quit/relaunch passes (PID3364→5341): disconnected startup/fresh counters, current embedded sources, two subscribers/no pending callbacks/errors; explicit Connect gets all six matching ACKs. Reopened base328x178 then Mapping328x312, main240x390 independent. Original context and bindings exact, checkpoint31 Values and registry exact after reconnect.

First checkpoint30 reload rounded three native Float Values by up to0.0000354; strict failure/deltas retained in project_restart_verification.json, no tolerance masking or forced Value restoration. Repeated31 restart is stable. Initial queued-load snapshot was captured before restart completed and excluded; accidental overlapping launch closed, final one TD process. Physical button/wheel/Escape, fixed cadence and deferred issue6 remain open;30-minute soak not rerun. project_restart_probe.py records raw phases and summary. No commit/push.

Final docs/exports refreshed and live checkpoint saved/verified: inspector_editor_actions.32.toe. Code hashes match the restart-tested31 checkpoint; final six ACKs, registry/Values and328x312 K2 Mapping retained. No pending UI callback.

### Compact Inspector physical button gate started (2026-10-08)

Verified active32, connected PLUGIN with six matching ACKs. Existing B1 Mask Image is Menu/Cycle with hardware adapter TOGGLE, initial value1 (Control); original six bindings unchanged. Existing main/Popup reused, selected B1 Mapping. External button_adapter_probe.py installs bounded pass-through receive/dispatch instance observers on the existing host, captures only B1 CC20 and post-dispatch target Values, no synthetic input/new MIDI ports/operators. One five-minute TDResources deadline removes hooks and saves physical_button_toggle.json; explicit Stop also removes them. No project save while testing. User must perform three presses (first held two seconds), confirm each toggles once/no extra hold/release action and LCD/LED. Physical observation pending. After reply read active probe or saved timeout artifact, stop hooks, then prepare input-only PUSH draft through the new Inspector; hardware TYPE change is a separate user action. Retain original TOGGLE adapter/value1 for final restoration. No acceptance claim/commit/push.

Physical TOGGLE trace stopped on user done: six B1 CCs/dispatches, user excludes first three mistakes. Corrected last three at58.759/61.226/62.692s have CC127/0/127, exactly three Cycle writes1/0/1, no extra dispatch/drop/observer errors. Native mapping valid; Value ends at original1. Raw first segment retained. physical_button_toggle.json records accepted corrected segment; LCD/LED not separately described.

B1 PUSH prepared through existing in-window HW Type dropdown and Mapping Apply: draft isolated, same host target/ID/ACK retained, no TX/unmap/re-LEARN and no other state/Value change. physical_button_adapter_setup.json records full before/after and restoration TOGGLE/value1. Recorder remains stopped until user changes physical B1 TYPE to PUSH in Roto-Setup and replies ready. Then Start(...,'push') for three press/release pairs (one held2s), check only rising presses dispatch; restore TD/hardware TOGGLE afterward. No save of temporary PUSH test configuration, no commit/push.

User confirmed hardware PUSH ready. Active32 verified, all six mappings ACKed; B1 TD PUSH/Cycle Value1, no error. Reused B1 Mapping Popup328x312 with current token; PUSH recorder started, one five-minute deadline, original catalog unchanged at Start. Await three physical press/release pairs (first held2s), then Stop and inspect CC127/0 pairs versus exactly three dispatches; user must confirm no release/hold action and report LCD/LED anomalies. Original adapter TOGGLE/value1 restoration remains pending. No project save or new operators/windows/MIDI processes.

PUSH physical trace stopped on user confirmation:12 CC127 presses,12 CC0 releases, exactly12 Cycle dispatches with alternating0/1 Values, zero release/extra dispatches, no drops/observer errors. User repeated several presses and confirms each switches once; holds/releases cause no extra switch. Observed wire hold durations0.099–1.335s (not a measured2s hold); LCD/LED not separately described. Raw trace/derived acceptance physical_button_push.json. Input adapter gate accepted in B1 Menu/Cycle scope; final hardware restoration pending.

Restored TD original TOGGLE through the same in-window dropdown/Mapping Apply: unchanged host target/ID/ACK, Tx156→156, Value already1 so no Value write, all six catalog rows exactly equal original TOGGLE test baseline. Recorder hooks/deadline removed. physical_button_adapter_setup.json records TD restoration; user still must change hardware B1 TYPE back to TOGGLE in Roto-Setup. Do not save a mismatched hardware/TD test state or claim hardware restoration before user confirms. No runtime source changes, new operators/windows, commit/push.

### Physical button gate closed (2026-10-08)

User confirms hardware B1 TYPE restored to TOGGLE. Active32 live verification: TD TOGGLE/Value1, all six original catalog rows exactly equal pre-test baseline, six matching ACKs, Connected/PLUGIN/Bindingvalid true, no error/LEARN/touch, two subscribers and no recorder/pending model work. Declared input adapter gate accepted in B1 Menu/Cycle scope; raw TOGGLE excluded/corrected segments and12 PUSH pairs retained, no synthetic packets. Source acceptance docs/gates updated; next refresh embedded docs/generic UI exports and save through live TD. Remaining replacement gates: fixed-cadence performance, physical wheel/OS Escape, deferred native resize6; native Style metadata conversion remains future Advanced scope. No runtime source change/commit/push.

Closed gate checkpoint saved and verified via live TD: inspector_editor_actions.33.toe. Source docs embedded, generic UI exports/reload pass with empty targets/offset0 and unchanged production MIDI session. Final original six catalog rows exact/all ACKed, B1 TOGGLE/value1, two subscribers, no recorder/geometry callback/operator errors, existing B1 Mapping Popup328x312 retained. physical_button_adapter_setup.json records final state; replacement_physical_gates.json input adapter accepted. No runtime changes or new physical checks beyond this gate; no commit/push.

### Fixed-deadline/native performance and synchronous publication (2026-10-08)

Active33 verified. Finite anchored10Hz forward/reverse18x8s ablations, sparse exploratory native10x8s, corrected burst-aligned native10x8s before/after and requested60Hz10x8s runs complete/preserve production. First sparse snapshots miss burst phase; retained as exploratory. Main redraw disable worsens cadence; fixture no-publication approaches idle. Sources/scripts/cadence_summary.json preserve distinct prefixes, raw samples and truthful failure limits.

Shipped candidate RotoPythonExt shares one detached snapshot per_publish for catalog/ACK/marks, and retains native CHOP channels on sample updates (rebuild on schema/OP replacement/missing changed channel). No authoritative deferral/batching, new timer or poll.239 runtime/118 Inspector tests pass;18 exact native fixture API writes verify synchronous Float/Int/Toggle outputs/catalog/no Pulse/no MIDI, original production unchanged. Two verifier setup mistakes (Int normMax initially1, unfired pulse counter absent) corrected and cleaned; final verification passes.

10Hz median wall-gap p95 Closed24.28→22.24, Fold23.73→22.31, Popup23.38→22.39ms. Corrected native Popup frame-work p9511.94→8.43ms, worst14.38→12.74; Window redraw3.25→3.35ms.60Hz most cases deliver~60Hz but Closed reverse14 delivers49.47 with74 synthetic producer deadlines missed; latest producer coalesces missed updates, no hardware loss claim.60Hz sampled dropped_frames0,10Hz candidate Closed reverse1. Uniform/full-rate cadence gate remains open; no30min soak/full process restart rerun.

Installed source through install_control_publication.py: clean Disconnect/reinit/Applybinding/Connect, original six catalog rows/Values/context retained, six matching ACKs, no idle projection callback; control_publication_install.json records before/after. Existing B1 Mapping reused. Next refresh embedded docs, generic controller/UI exports and save live checkpoint. No commit/push.

Generic controller exports/roto_python.42.tox reload verified disconnected with empty catalog/channels and current embedded source; production process/catalog preserved. Initial same-tick pending-callback assertion was premature: Applybinding queues one optional end-frame projection. Staged read-only reload verification waits for native frames and confirms callback clears without forcing cancellation. No export overwrite. Generic UI exports/reload pass; two subscribers and original six catalog rows/all ACKs exact. Existing B1 TOGGLE/value1 Mapping restored at328x312, main240x390; no fixture/geometry callback/operator errors. Final checkpoint saved through live TD and file verified: inspector_editor_actions.34.toe. Evidence control_publication_export.json / control_publication_checkpoint.json. No commit/push.

### Advanced first-slice planning (2026-10-08)

User defers performance and agrees to native metadata inspection/editor access first, invoking td-build-planning. Active34 read-only scout verifies six ACKs/idle control, Follow on, existing four editor hosts/model shortcuts, scoped zero-wire graphs and module/section bounds. Local Par/OP/UI docs confirm Style read-only, separate slider/clamp bounds/default behavior, openParameters Value dialog versus openCOMPEditor custom definition editor. ADVANCED_PLAN.md allocates one shared module and existing Details readout/footer additions, fixed section224/base178, detached snapshots/on-demand reads, stale-target guards, phased native verification and later metadata/Style slices. No runtime UI installed, dialog opened or project saved by this planning pass.

Global scout finds retained parent save warning from the now-destroyed base_control_publication_export fixture: its stored Popen object contains an unpicklable thread lock. Corrected diagnostic script on disk to store/compare scalar PID. Inspector/controller child roots remain clear; no claim of clearing the historical parent warning or rerunning generic exports. No controller mappings/Values/process changes, commit or push.

### Advanced native readout/editor slice installed (2026-10-08)

Implemented parameter_definition.py once under shared base_commands, guarded ParameterDefinition/OpenNativeEditor model/command APIs and local view snapshots. Existing Details now starts with native name/Label/Page/Style/default mode/value/source, separate slider/clamp limits, eval/readOnly/Bind ownership and eight-option Menu preview/count. Five24px bundled MDI footer actions add Values/openParameters and Definition/openCOMPEditor, with hover names/reasons. LEARN/touch, stale context/session/owner guards; no metadata setter, auto native dialog, Value/Pulse/MIDI write or per-frame metadata polling. Defaults/native edits update on Refresh/reopen. Fold/Popup reuse fixed224px Details delta, base178/Details402/Mapping312 and internal scroll.

Native screenshot found402px Window with178px root, clipping Details/stretching upper controls. Programmatic section transitions now synchronize panel-root height; existing intended geometry/three-frame settlement remains. Unit/native/CUA verifies matching402px root and content y0 with visible fixed text. Manual drag deformation#6 stays deferred.239 runtime/127 Inspector tests pass, including8 new native snapshot/command cases and1 root-height regression.

verify_advanced staged isolated fixture passes seven native target types, both styles, default edit/Refresh, no metadata reread on Value updates, wheel/guard/callback/empty states and unchanged production catalog/registry/routing/process/session. One harness COMP.adapter typo and a docked-DAT inspection mistake corrected; fixtures cleaned. CUA observes correct Values/Definition dialogs, each opened twice to the same owner and closed once back to Inspector; Follow on/pane/routing preserved. No native dialogs/fixture remain. Fresh external builder opens no test windows and returns two subscribers. Measured four-host network cleanup recorded advanced_network.json.

Generic reload initially catches fields builder resetting accepted inline opener callback timing. Corrected build_live order installs context_menu after all fields/sections; full upgrade and unchanged generic header/editor callback assertions now pass. Generic UI exports embed current module/docs and clear native snapshots/labels/values/actions; real MIDI stays connected, six mappings/ACKs unchanged. Source report ADVANCED_REPORT.md; evidence advanced_install.json / advanced_verification.json / advanced_builder_verification.json / advanced_network.json / live_export_reload.json. Final checkpoint saved through live TD and file verified: inspector_editor_actions.35.toe. K2 Details328x402 open, root402/content y0, fifteen rapid178↔402 cycles stable, original six catalog rows/Values/all ACKs exact and same real MIDI process. No commit/push, extra stress or full restart.

### Details footer placement (2026-10-08)

User requests more comfortable placement at bottom-right. Five existing Details actions now use right anchors in all four Fold/Popup editor hosts: 24px icons,6px gaps,12px right inset,y6. build_parity.py preserves placement on future builds; install_details_footer.py applies the narrow change without rebuilding editors. Native screenshot confirms bottom-right actions; live assertions check all four hosts and scoped Inspector errors are clear. Generic UI exports and embedded README refreshed through live TD, real adapter restored and K2 Details reopened. No runtime/controller change or extra stress test. Checkpoint saved through live TD: inspector_editor_actions.36.toe.

### Reveal crosshair correction (2026-10-08)

User reports crosshair has no navigation effect. Active36 live repro: Follow true, Reveal disabled, direct Action returns Follow guard, pane remains /inspector_model. Removed guard in UI and adapter. Reveal clears target's selected children while Follow is on before entering target COMP, preventing saved child selection from routing to another Device; preserves Follow preference, homes without zoom, and falls back to an existing open Network Editor when current pane is not one. Invalid/missing target/editor still returns an explicit error; stale command tokens remain validated.

Four regression tests fail before fix/pass after;239 runtime and131 Inspector tests pass. Actual CUA click on Popup crosshair navigates to /roto_control_python/pixelSortV3 with Follow on; production catalog/Values/registry/process/session exact and two subscribers (reveal_verification.json). Source DAT updates automatically reload Inspector extensions and initially leave blank editor; corrected installer description and reopened K2 Details after settlement. Production controller not reinitialized. Current source docs embedded, generic UI export/reload strict gates pass; loaded Reveal tested again, scoped controller/model/view errors clear. K2 Details retained, pane at pixelSortV3. Saved through live TD as inspector_editor_actions.37.toe. No commit/push or extra stress test.

### Reveal locates COMP node (2026-10-08)

User clarifies Reveal should locate the COMP node, not enter its contents. Adapter now uses target.parent() as pane owner and home(zoom=False,op=target); Follow-on destination selection clearing applies to that parent network. Regression expectations updated: old inside-COMP behavior fails;239 runtime/131 Inspector tests pass with parent-node centering. Native Popup click verifies /roto_control_python parent network with target pixelSortV3; Follow/catalog/registry/process/session unchanged. First click on inactive Popup does not dispatch; next click does. Initial cross-network zoom equality assertion fails because TD restores destination network's stored zoom; repeated Reveal preserves that destination zoom, and docs now describe this accurately. No forced zoom/target selection.

Generic UI exports/reload pass; loaded action centers COMP in parent network, K2 Details reopened and scoped errors clear. Evidence reveal_verification.json refreshed. Checkpoint saved through live TD as inspector_editor_actions.38.toe. No controller reinitialization, commit/push or extra stress.

### Reveal readable zoom (2026-10-08)

User requests larger network scale after locating COMP. Active38 pane zoom0.102. Reveal now explicitly sets pane.zoom=1.0 after home, retaining parent-node centering and Follow-safe navigation. Regression simulates home lowering zoom to ensure final1.0 assignment occurs afterward.239 runtime/131 Inspector tests pass. Three consecutive live actions keep parent network/zoom1.0 with exact catalog/registry/MIDI process; generic UI export/reload passes, loaded Reveal also finishes1.0. K2 Details reopened; scoped errors clear. Docs/evidence refreshed. Saved through live TD as inspector_editor_actions.39.toe. No commit/push.

Reveal zoom correction before completion:39's immediate post-action checks were insufficient. Next-frame/save verification catches zoom falling to0.5 after native home, so39 is an intermediate failed viewport attempt. Removed home entirely; set viewport zoom1.0 and x/y directly to target node center. Native screenshot confirms readable pixelSortV3 node at parent network; following-frame assertions retain1.0 and330/65. Regression now forbids home and checks fixed scale/coordinates.239/131 tests pass again; current source generic export/reload passes, reopened K2 Details/loaded Reveal and settled geometry checked. Final checkpoint40 saved through TD and verified after save. No repeating native home/zoom animation, controller change, commit or push.

### Inline native Label/default draft, 6b first slice (2026-10-08)

User says next after Reveal readable zoom40. Loaded td-build-planning; DEFINITION_EDIT_PLAN.md scopes independent scalar Float/Int Label/default before bounds/Menu/Style. Implemented shared definition_edit, command/model APIs and pencil/form inside existing Details native group. Native draft152px/fields90px fits fixed178px viewport; editor402/main390 unchanged, no new Window. ✓/× use bundled MDI icons/release-inside callbacks. Draft strings/state scrub on Close/export/init, fresh hardware LEARN/touch plus active context/session/mapping token and exact native owner/group/index/default/slider/clamp fingerprint guard Apply. Clone/Bind/group/evaluation unsupported cases report reasons. Only changed Label/default setters; readback/rollback errors reported. No live Value/Mapping Label/range/id/hash/ACK mutation or controller Configure/offer/re-LEARN.

239 runtime/139 Inspector tests pass. Native disposable Float/Int setters/restoration/stale draft verification plus real K2 no-op Apply/cancel preserve original catalog/registry/process; fixture removed, two subscribers. CUA Default text entry0.5 changes only draft while native default0.25/live0.4872123543 remain, then cancelled. Fold/Popup fixed dimensions verified. Native screenshot led to trimming form112→90/group192→152 to avoid clipped actions. Minimal mocked view close initially lacked _draft; lifecycle-safe discard fixed. One unittest invocation from repo root finds0 tests; correct src/touchdesigner and prototype directory suites pass. Measured cleanup annotates shared module/four draft subcontainers; scoped errors clear, model graph0wires/no cycles. Native extension reinit explicitly discards unsaved draft. Generic exports/reload embed module and verify empty draft strings/state/hidden forms. No production metadata mutation, full restart/stress or physical Reset-to-default acceptance claimed.

Source DEFINITION_EDIT_REPORT.md / definition_edit_verification.json. K2 native Label/default draft open for review, original0.25/Low Threshold intact, six ACKs preserved. Final checkpoint saved through live TD: inspector_editor_actions.41.toe. No commit/push.

### Native slider/clamp bounds, 6b continued (2026-10-08)

User says next after41. Extended independent scalar Float/Int definition draft with normMin/normMax,min/max,clampMin/clampMax. Folded BOUNDS area uses same Apply/Cancel, form90→174px and fixed Details402/main390 with internal scroll. Fresh bounded4096 current-controller library scan covers active catalog, saved Devices/Tracks/Layouts and page targets; active context/ID overrides saved entries, active tombstones excluded. Real K2 has two saved mappings at0–1. Compatible proposed clamps must cover all matching mapping endpoints, Default and latest raw/constant Value; changed relevant library or already-clamped Value blocks Apply. No Value overwrite, controller Configure/offer/re-LEARN or mapped identity change. Shared metadata caches refresh and view token renewed before updated readout. Error uses readable saved Mapping range rather than UUID. No-op Apply reports unchanged.

239 runtime/149 Inspector tests pass, including ten new bounds/library/view-token cases. One test callback entry lacked id; bounded scanner now skips callback paths safely while still counting toward cap. One root-directory unittest invocation found0 tests and one wrong relative append path failed; correct-directory suites and corrected view harness pass. View harness originally omitted CloseContextMenu stub; corrected without changing runtime behavior. Native disposable Float/Int sliders/limits/clamp switches change/restore, with unchanged default/live Value. Real K2 max0.5 correctly rejected because existing Mapping0–1 exceeds it; following no-op Apply restores draft, no native mutation. Actual CUA clamp toggle and slider-max text2 affect only draft (native ON/max1 retained), cancelled. Both styles/three folding cycles retain sizes; no fixture left. Measured cleanup/no-overlap for four draft hosts. Generic export/reload verifies all eight draft strings/flags empty and state/form hidden; two subscribers, scoped errors clear, original six mappings/ACKs/registry/MIDI process preserved. Current source docs/evidence DEFINITION_BOUNDS_REPORT.md / definition_bounds_verification.json.

K2 BOUNDS draft open for review, original native0–1/default0.25 remains. Saved through live TD as inspector_editor_actions.42.toe. Static Menu labels next; Style migration separate. No commit/push, physical re-LEARN, full restart or additional stress.

### Static Menu labels,6b continued (2026-10-08)

User says next after42. Installed labels-only draft for independent scalar static Menu2–24 choices in existing Details. Fixed names/count/order/default/Value; same compact MDI Apply/Cancel and24-row pools with internal scroll. Existing wire identity includes Menu labels: ConfigureControl rebuilds only the active binding, retains stable ID/index/mode/input/range, clears old hardware semantics and sets Needs re-LEARN. No automatic offer/LEARN. Inactive snapshots intentionally retain old choice/hash metadata; browse shows pending re-LEARN, activation refuses old identity restoration, existing page-recall guard rejects old labels. Exact full24-choice native fingerprint, relevant library and fresh hardware/context/session checks; setter/controller failure attempts native and binding compensation, reports partial failure without Value rollback.

239 runtime/159 Inspector tests pass. Native disconnected controller verifies active replacement, unrelated mapping, inactive projection/activation, old ACK rejection/matching ACK clears prompt,24th-label Apply/Cancel and both views. Actual CUA scroll/keyboard/Apply passes. Real K1 cancel/no-op Apply in both views preserves six ACKs; fixture removed, original registry/MIDI PID38487/two subscribers/scoped errors preserved. One wrong relative test-file path failed before corrected suite; inactive fixture without state now uses optional state projection. Second geometry run hit626px from source-reinit/closed-window stale cache; explicit178px fixture setup then402px settled assertions pass, no broader lifecycle/resize fix claimed. See DEFINITION_MENU_REPORT.md / definition_menu_verification.json. Remaining next scope is isolated Style migration; physical renamed-label LCD/re-LEARN acceptance and full replacement remain open. No commit/push, restart or extra stress.

Final checkpoint saved through live TD as inspector_editor_actions.43.toe, verified after save. Real K1 Sort By static Menu draft open for review, unchanged original labels/eight choices and six hardware ACKs. Current generic UI exports/reload contain no native choice/draft information.

### Lossless native Float/Int Style6c (2026-10-08)

User asks to continue and do manual verification once together. Added STYLE_MIGRATION_PLAN.md and disposable Page replacement scout: same Par/index survives Float→Int→Float, but attributes/value reset. New shared style_migration at700,0, measured880×175 command annotation. Native draft Style selector uses existing in-window Float/Int rows, same Apply/Cancel, normal154/preview172px native group in178px viewport; fixed402px Popup/390px main. Local Nativestyle and one event-driven draft callback inside each base_draft; no per-frame Style scan. Exact native metadata/preview Value and related registration fingerprint/fresh session/context/token/hardware guards; Controls validates detached proposed definitions before setters. Foreign standard controller registrations, stale binding type/Value and unsupported/fractional conversion block. Active watcher paused/restored; existing ConfigureControl unchanged. Stable IDs/index/ranges/mode/input remain; related inactive/off-page canonical identities rewritten with Needs re-LEARN to reject old hashes. No automatic Ping/LEARN. Full supported metadata, native Par identity/page/order and Value restored/read back; failure compensates binding/library, leaves cleared hardware pending, reports incomplete restoration.

239 runtime/179 Inspector tests pass (20 new cases). Native offline controller batch verifies both conversions, existing Par/path-expression reference, full metadata, other-controller block, unrelated binding, inactive/page identities, old ACK rejection/new ACK clears prompt, new page recall/return and injected registry-save failure with native/binding restore. One initial native setter attempted read-only hidden and rollback also failed there; disposable fixture removed and exact production preservation verified, then hidden preflight-rejected/read-back-only. Runtime checks were not weakened. Added guard for cached runtime Value/type and detached preflight of all related saved Controls. CUA dropdown downward/one item click and actual Apply pass, Value3 preserved/Int input/re-LEARN/402px. Real K2 default0.25 and Value0.4872123542696698 reject Int in both styles, cancelled with exact original metadata/all six ACKs/catalog/registry/MIDI PID38487/two subscribers. Fixtures removed; scoped errors clear.

Sources STYLE_MIGRATION_REPORT.md, style_api_probe.json / style_migration_verification.json; generic export/reload includes helper and scrubs Style strings/captions/preview. ACCEPTANCE_BATCH.md groups remaining physical Menu labels and actual numeric Style/LCD/re-LEARN in one future temporary Device, with original-state restoration. No production test bank created or physical acceptance claimed; other Style migrations, full replacement, performance and resize gates remain open. No controller restart, extra stress, commit or push.

Final checkpoint saved through live TD as inspector_editor_actions.44.toe, verified after save. K2 original native Float/default0.25/Value0.4872123542696698 draft open for review, six matching hardware ACKs preserved. Generic UI exports/reload scrub all Style state/captions and embed current preflight helper.

### Explicit compact Device activation, 6d (2026-10-08)

Next slice after lossless native Float/Int44. Added shared ActivationToken/ActivationCapability/Activate and TD adapter using one existing SelectPlugin(full Layout/Track/Device key), with fresh session/routing/deletion and LEARN/any touch/LOCK/dispatch/paused/backlog/pending/gated/transport guards. Offline library selection supported without a running transport. Inactive-bank Activate shares existing80x16 bottom-right footer space with active Clear Device; selectors remain browse only and LIVE returns to routing. Follow preference and Network Editor selection unchanged. Two native panel nodes per view, no new Window or frame poll; external installer/builder sources embedded.

Eight new tests:239 runtime/187 Inspector pass; git diff --check pass. Isolated disconnected clone/native controller APIs test Device, Track and Layout switching without Value writes, freshly changed guards, stale session, real install failure/original routing rollback and next-flush fence recovery, unchanged-selection Follow semantics, explicit Fold/Popup footer states. CUA native click changes BROWSE to LIVE/Clear Device. Initial fixture name exceeded12-byte hardware limit and rollback injection confused flattened Layout id with Plugin id; corrected. Immediate recovery assertion moved to existing controller flush. A reused CUA binding after window changes produced a non-dispatched click; rebinding current window produced the expected single-click result. All fixtures removed/production restored after attempts. No real MIDI or production bank activation in verification.

Native source/export checks pass, generic activation hidden/unconfigured and commands/live model/UI current. New nodes/annotations measured without overlap; model/views/controller scoped errors clear, command graph6nodes/0wires/no cycles. Root function/overview Markdown and prototype README embedded. Original six matching ACKs/catalog/registry/Values/session preserved, real MIDI PID38487/subscribers2, Follow false preserved. K2 Details402/root402 reopened. Saved through live TD as inspector_editor_actions.45.toe and actual file/post-save geometry verified. Evidence activation_verification.json/live_export_reload.json; source ACTIVATION_PLAN.md/ACTIVATION_REPORT.md. Physical LCD/recall joins one final ACCEPTANCE_BATCH; no human gate requested now. No commit/push, resize work or repeated soak.

### Ownership/selection contract integrated; management plan (2026-10-08)

Received completed investigation from c2c61952-def7-4ca5-8ff7-6609629f12e8. Read root-checkout docs/plans/inspector-context-contract.md and GLOSSARY.md plus boundary/hardware research; source paths remain /Users/huihongnin/project/roto_control. Contract is uncommitted there and not assumed part of PR14. No external worktree or shared live TD changes in this handoff integration.

Layout COMP/CUSTOM ownership, Track/Device/control-page navigation, Browsed context, committed Routing and independently selected/pending hardware fields are separate. Device-first is presentation. Existing v3 ownership is Legacy/unclassified, not inferred from CUSTOM name/Focus. .45 Browse/Activate/LIVE contract retained; LOCK source-policy differences preserved, no force-select. Naming design blocker resolved; #9 durable owner/clone/unregister/relink/default-variant prerequisites remain for owner-dependent management.

Added MANAGEMENT_PLAN.md with one shared command interface, source-audited manager guards/name limits/manual naming/successor rules, revision/confirmation requirements and staged Rename-first plan. Create Custom and owner-sensitive Layout deletion stay unavailable until metadata/lifecycle supports them. Source audit notes nonuniform Rename guards and possible partial save/transport side effects; no transactional claim. ACCEPTANCE_BATCH now integrates one original pixelSortV3→fractal_pop→pixelSortV3 SEL/FUNC/Browse/Activate trace after temporary Style/Menu target cleanup, without duplicate accepted hardware gates. Root cause remains unverified; full candidates vs visible bank reset recorded separately.

This integration changes source planning Markdown only. No management UI/runtime build, docs embedding, exports/checkpoint, tests/native/physical claims, commit/push or GitHub modification. Runtime baseline stays inspector_editor_actions.45.toe. Next implementation slice: guarded registry Rename with explicit linked-device manual naming, preserving IDs/hash/library/Values/Focus/routing/Follow and compact in-window presentation.

### Issue9 source-only ownership handoff noted (2026-10-08)

Received informational implementation handoff from /Users/huihongnin/.t3/worktrees/roto_control/t3-issue-9-comp-custom-layouts, branch t3/issue-9-comp-custom-layouts/baseline1cb09d9. Read its stable issue-9-owner-layouts contract and API/selection/revision source plus prepared native checklist; no imports/changes in that worktree, no shared TD calls, source installs, unit/native/physical reruns, exports/checkpoints, GitHub mutations or commit/push. Reported252 source tests are not integrated239-runtime/187-Inspector evidence. #9 remains pending acceptance; #11 dependency is not cleared.

MANAGEMENT_PLAN now records additive ownership schema/API/lifecycle and source acceptance gates. Read-only integration finding: source permits same-key SelectPlugin after bound-owner return to reconstruct quarantined controls, but .45 already-active capability/footer blocks that recovery entry. Formal integration must expose explicitly guarded same-key recovery and fresh owner/quarantine status, without auto activation or false ACK readiness. Also raw revision includes captured state/observations; distinguish semantic management draft fingerprints from backend serialized revision check. Detached full-library GetPluginTargets must not overwrite16 current slots with reused off-page slots. Direct owner Layout/entry Track/entry Device delete stays forbidden; unregister is a tombstone, not destructive deletion. Preserve qualified variants and both source baselines before native deployment. These are plan findings, not runtime changes. Artifact baseline remains45.

## Issue #12 Action presets — reviewable source only (2026-10-08)

- Worktree: `/Users/huihongnin/.t3/worktrees/roto_control/t3-issue-12-action-presets`; branch `t3/issue-12-action-presets`; base HEAD `1cb09d983f970fe4cc01b85639c7baccecd8b092`. Uncommitted/unstaged diff; no commit/push/merge. Docs PR #14 read through gh as spec, not cherry-picked.
- Stable consumer contract in `docs/functions/actions.md`: RegisterAction / AssignAction / RecallAction / GetActionState / GetActions / UnregisterAction; reconstruction hook `registration.onRegisterActions` in both setup modes. Mapping identity and action identity are separate. Existing CUSTOM/COMP-linked Layouts supported without #9 ownership allocation.
- Existing Button dispatch/latch/fences/LEARN/ACK are reused. Structured validation_failed/execution_failed/partial/unavailable results and JSON-safe provider readback details reach control/Inspector diagnostics; success alias normalizes to succeeded. Failed hardware recall suspends only that Button; true parameter feedback is refreshed after success or partial writes. Consumer side effects have no rollback guarantee.
- `test_action_presets.py`: 21 new source tests. Full `python3 -m unittest discover -q` from src/touchdesigner: 251 tests / OK. Source syntax and Markdown/diff checks passed. These use fake TD handles and synthetic MIDI, not native/physical evidence.
- `diagnostics/runtime/verify_action_presets.py` is a prepared, unexecuted native harness: build disposable source fixture, test actual Par feedback and independent existing contexts, structured failure, registration repair, native tox save/load and empty generic export reload. A valid external Python path is explicit. During the coordinated native window: execute the script, `build_fixture(explicit_test_parent, this_source_dir, python_path)`, wait a TD frame, `exercise(holder)`, wait, `holder = save_reload(holder)`, wait, `finish(holder, new_evidence_path)`. `cleanup(holder)` handles fixture failure; no Connect/physical ports or canonical artifact promotion. Coordinate with Inspector before execution.
- Native TD/errors/actual reload/export and physical Button PUSH/TOGGLE/LED/LCD/motor gates are **pending**. No shared live TD, user mappings, upstream Ableton/Bitwig, licenses/reference PDFs, canonical toe/tox or other thread worktrees were modified. #12 stays OPEN and #13 native blocked_by dependency remains unsatisfied; handoff does not authorize #13 implementation.

## Issue #12 resumed on accepted #9/Inspector source (2026-10-08)

Safe fast-forward to `61d0e03fc454dba496618fdf33ab4a5169437b19` in the app-bound `t3/issue-12-action-presets` worktree after verified scoped archive/stash. Original archive `/var/folders/5q/krg7wb4d4lsgpmlmgqvywj_w0000gn/T/roto-issue12-precompose-ai24dd0e`, retained stash `4d61c2a0de94836ca7452c76ed8093975e9c2da2`; original 13 file bytes/manifests preserved. Four compose conflicts (HANDOFF/extension/internal Inspector/export) resolved by hunks, retaining accepted owner ingress, quarantine, live-value publication, ACK/output-channel behavior and all original handoff entries. No own commit/push/close or shared TD calls.

R1 immutable source review found one Standards P1 (software recall lacked required owner/quarantine guard) and two Spec findings (same authority gap and current Inspector/inactive action projection). These are fixed: explicit recall freshly checks owner/quarantine; active/inactive Action identity/availability/results reach the current Inspector, provider readback details notify without assignment-token invalidation, Pulse-only schema is retained, stale prior success never displays as current availability. Publication shares the existing detached observation with outputs instead of adding repeated parameter scans. Real COMP-owned/CUSTOM independent mappings are source-tested.

Source now passes 300 runtime and 215 Inspector tests; 24 Action runtime + 4 Inspector cases augment the accepted 276/211 common base. Failed source attempts are retained in tool history: active-owner unregister was correctly rejected by #9 guard (fixture switched away/unregistered, then simulated persisted active restoration); the returned-owner fixture initially lacked explicit capture under a mocked publisher (added legitimate capture); importing an existing TestCase class duplicated five Inspector cases (changed to module import). Checks were not weakened. Native fixture was adapted to a real COMP-owned Layout; syntax/source checks only. R2 independent review and immutable final pin are next; all native/physical Action gates remain pending and #13 remains blocked by OPEN #12. Root is sole delivery/native executor.


## Issue #12 fixture artifact preservation correction (source only)

Root identified that the earlier prepared harness destroyed build-failed holders and deleted verification tox copies on finish/cleanup. Corrected `diagnostics/runtime/verify_action_presets.py` without changing the Action runtime/public API: unique retained artifact directory; actual reload/generic tox paths, sizes and SHA-256 recorded in success/failure evidence; errors captured before fixture-local callbacks/source sync/session are stopped. Stage failure leaves the failed holder and generic nodes inspectable. Normal save/destroy/load remains the actual reload test, with a serialization checkpoint and retained disk copy before destruction. `finish` now records evidence and leaves nodes; executor inspects/captures any additional recovery, then explicitly calls `cleanup(holder)`, which requires matching fixture evidence and deletes nodes only. No saved toe/tox/export/evidence is unlinked. Quiesce errors refuse successful finish/destructive cleanup. Seven synthetic disk/lifecycle regression tests do not constitute native acceptance. Bounded delta review found missing/unreadable artifact hashes could still report success; corrected evidence marks failure and blocks finish, pre-reload destruction and cleanup until copies can be hashed. One initial source test command used the wrong working-directory-relative path and did not edit/run the new tests; corrected scoped patch and six tests pass. Earlier 17-file immutable pin remains untouched. No TD execution, physical check, commit/push/close or dependency change.


## Issue #12 queued native fixture API/ACK correction (not executed)

Inspector read-only pre-execution review found redundant `SetPluginComp` on RegisterComp's owner entry; the accepted common-base API correctly forbids it. Removed that write and now assert COMP category, bound/non-quarantined owner, entry Plugin identity, qualified link metadata/path and the actual identical owner/Focus handles. No relink or owner guard relaxation. Fixture TOGGLE stage now explicitly refreshes LEARN/offer/matching ACK, asserts mapped/new adapter and zero recalls through configuration/ACK/LEARN input/exit, before unchanged three valid press counts. Source audit confirms current button_type-only ConfigureControl is local RX adapter and retains wire identity/ACK; no runtime rule or ACK parser changed. Two added synthetic checks exercise real source owner guard/entry observation and zero-recall adapter/ACK sequence. Initial negative owner test injected a stale handle that GetLayoutContext correctly refreshed; revised to pass the genuinely wrong consumer handle, preserving the authority check. All old pins remain immutable. #12 native not started; root must verify new exact pin and explicitly resume only after baseline restoration/checkpoint. No TD/source install, physical, feature commit/push/close or #13 implementation.


## Issue #12 actual scheduled result-details failure and bounded source correction (2026-10-09)

Inspector/root recorded an actual disconnected native FAIL: first succeeded result entries.actual_value=.71 reached scheduled Sync26→28; second same-status .72 updated GetActionState/database but targets SHA stayed identical, Sync stayed28 across frames88456→89175, Info stayed.71 and assignment token unchanged. Read-only evidence `/var/folders/5q/krg7wb4d4lsgpmlmgqvywj_w0000gn/T/roto-issue12-native-20261008T193240Z-4mqgqcpa/native_scheduled_details.json`; manualSync=false/physical=false. Preserve this FAIL and holder/tox/pin/recovery history; r5 native overall is not accepted, dependent reload/export/#11 are held.

Applied diagnosing-bugs: deterministic red replay executes the real runtime publisher, actual build_live DAT observer configuration/callback text, RequestSync/SyncController and end-frame view dispatch using fake TD DAT/run boundaries (no TD imports). Database becomes.72 and targets remain identical, but no observer notification/Sync occurs; repeated red confirmed, including final regression run against immutable r5 inspector_data in memory. Boundary probes show only _flush_inspector scheduled. A normal context metadata event (diagnostic probe only, not manual Sync/acceptance) delivers.72, distinguishing missing signal from publication/scheduler/projection failure. Source correction places detached GetActions diagnostics in both publication signature and existing context_state payload; existing ControllerMetadata observer now signals unchanged-status nested results, including actions only referenced in inactive/off-page contexts. No blanket database observer, periodic force Sync, builder/geometry/routing/dispatch change or Layout registry mutation. Full root-cause reasoning, red command/probes and native limits are in docs/plans/issue-12-scheduled-details-diagnosis.md.

Four scheduled-ingress regressions cover same-status nested readback, status/error/revision/entry burst coalescing with one model observation and stable detail token, inactive/off-page result with unchanged current table/database and no slot union, parameter-only metadata stability and action-identity token invalidation. Full runtime309 and Inspector219 source tests pass. These fake event boundaries do not prove the actual native chain fixed; root verified replacement pin + full restored checkpoint + explicit Inspector sole-executor start must re-run the original fresh-frame actual symptom before dependent tox/reload/export or physical gates. No TD/live/other-worktree edit, Connect, project switch, feature commit/push/close or #13 runtime/blocker change.


## Issue #12 Action provider-error/token correction (2026-10-09, source only)

Root/Inspector r6 attempt4 actually closed the original same-status scheduled.71→.72 symptom (Sync5→6, unchanged targets/token, both resolved WeakMethod views). Preserve that bounded PASS, root-qualified r5/observer-template evidence and every old bundle/attempt; it is not full native acceptance. Companion native burst partial/error/revision4/readback.75 delivered to both views with one model observation/Sync+1 but metadata mask256 and changed assignment token; exact equality gate failed and holder retained. Authoritative attempt4 files/SHA hashes are preserved in new bundle evidence, at `/var/folders/5q/krg7wb4d4lsgpmlmgqvywj_w0000gn/T/roto-issue12-r6-native-20261008T200258Z-7kmvo1uj/attempt4`. Dependent tox/reload/export/physical/#11 remain held, #13 blocked.

Diagnosing-bugs red uses real RecallAction/Actions result -> GetControlState/GetControlCatalog error -> TDControllerAdapter.Read -> metadata_signature -> actual installed builder callbacks/RequestSync -> two WeakMethod view callbacks (fake TD pars/DAT/end-frame runner, no TD import). The prior fake burst case mutated nested action_result while leaving top-level error empty, missing the actual producer. Repeated red produced(256,256) rather than(256,0); only META_FIELDS.error changed, valid/mapped/action availability/session/identity stable, one Sync/observation. Final regression also runs red against r6 getters/fingerprint loaded in memory. Correction adds explicit mapping_error provenance to current and inactive Action projections/catalog; existing complete error and action_result stay visible. Action fingerprint uses mapping_error only when authoritative string is present; unknown/older projections and non-Action generic errors retain conservative error fences. Provider observation error is display-only; true availability remains metadata. No Action API/dispatch/owner/ACK guards, r6 context_state ingress/coalescing, watcher/geometry/generic lifecycle change.

Software partial/error→succeeded/error-clear now preserves exact token, both view details and failure health, one Sync/observation. Hardware partial remains invalid/unmapped with nonempty mapping_error, rejects stale commands and unacknowledged presses, repair retains honest failure history until fresh ACK/valid retry. Supplemental descriptor/availability/identity/session/generic-error checks remain fenced via existing parameter watcher callbacks. Initial fixture bugs were kept in tool history: base_targets/targets was incorrectly resolved by a suffix-only fake inspector router; corrected exact path routing. Supplemental descriptor/session tests lacked their real parameter watcher signal; replayed existing builder mode/value callbacks instead. Fake promoted WatchOwners/WatchPars methods added to the test model COMP proxy. Initial JSON probe rejected immutable Health mappingproxy; captured detached dict instead. Strong software chain covers both disconnected/unacknowledged and acknowledged controls; initial expected saved health in the unacknowledged fixture was correctly relearn, so assert the existing requires_relearn fence/health rather than clearing readiness. No guard/assertion weakening or native execution.

Full source runtime311/Inspector223 PASS. New authoritative source package is reconstructed from exact full GitTREE, without generated pyc; prior cache-containing mirrors remain intact and must not be described as complete trees. New pin/root verification + fresh restored baseline checkpoint + explicit Inspector sole-executor start are required for actual partial/error→success token gate before dependent lifecycle/physical. No live/import/install/other-worktree edit/commit/push/close/dependency change.

## Issue #12 harness-only inherited extension quiesce correction (2026-10-09)

Root accepted r7 actual provider-error/token closure: five corrected-table-audit phases, exact token/display256/metadata0/two real views/one Sync, bounded synthetic guards and fresh pixelSort6 restoration. This is bounded native closure, not lifecycle/physical acceptance. Preserve r7 TREE245dd871f546962c5b452d680d78640965e682e0 and all old evidence/pins. RUN7 `/var/folders/5q/krg7wb4d4lsgpmlmgqvywj_w0000gn/T/roto-issue12-r7-native-20261008T204700Z-5ycffs4q/pinned_quiesce_native_lookup_warning.json` SHA2561141e4c140afdd31f4380c6930458c8ac1c25a76f773a4ebffbbecccaded0f44 contains422 descendant missing-Disconnect errors. Executor secured the holder with explicitly scoped external controller Disconnect/Execute/sync disable; original warnings and recovery retained. No Action runtime regression proven.

Diagnosing-bugs repeated source RED at the actual harness lookup seam: fake TD ext resolves an inside/outside ancestor extension, but the descendant has no owned Disconnect. Minimal holder-only inheritance still reproduces. Boundary probes show both actual local source/generic owners disconnected once, all callbacks/sync/load already stopped and external host unchanged; errors come only from inherited non-owners. The correction adds an authoritative extension.ownerComp == node guard before Disconnect/host disable. It does not infer ownership from node names/paths/display labels, mask error strings or remove strict assertions. TD ext parent search is documented in [Derivative Extensions](https://docs.derivative.ca/Extensions); the actual runtime sets ownerComp on its extension. True owned extension-access/owner-access/Disconnect/host-disable and callback-stop errors remain captured and prevent finish/cleanup. Native operator lookup/equality remains the next actual gate; source fakes do not constitute that pass.

Three new source lifecycle regressions cover inherited lookup including an inherited promoted Disconnect, source and loaded-generic local owners, Execute/sync/load order, external host untouched, genuine failures retained with stage-native-errors/artifact hashes before cleanup, and actual harness finish success/failure plus strict cleanup and retained saved copies. An injected callback-stop failure initially counted only successful fake Disconnect completion; the fake now counts invocation before asserting order, retaining the genuine stop/order failure rather than weakening checks. Full runtime314/Inspector223 PASS, source-only; original r7 quiesce loaded in memory remains red. Only diagnostics/runtime/verify_action_presets.py/test_action_presets.py/this scoped HANDOFF differ from r7; Action runtime/public API/backend/Inspector/owner/ACK/builders remain byte-identical.

Root's r7 evidence qualification supersedes the original overbroad unchanged-table request without editing old pin/evidence: same-status/details-only with unchanged error/readiness/unmapped Readback requires full targets SHA exact; succeeded↔partial/error permits only expected Action-row Value/Error display deltas, records full SHA and row cells, and preserves other cells/identity/range/definitions/library/routing/availability/ACK/session/token, display256/metadata0/one Sync. True hardware/availability/identity guards have separate expected invalidation. Honest diagnostics are not suppressed.

Next root-coordinated gate after exact replacement pin verification + restored checkpoint + explicit sole-Inspector resume: small actual native_local_quiesce owner inventory proof before remaining inactive/lifecycle gates. Separate external inactive setup qualification is not a source fix: replaced same-kind slot/id mappings enter removed_controls and disappear from library; register the off-page provider after final routing/reconstruction or through the existing complete registration hook, then require availability true and settled identity/token before recall. Do not retain legitimately replaced IDs or prevent registry rebuild. No TD/import/Connect/source install/other-worktree edit/commit/push/close/#13 runtime. Physical/#11 remain held, #12 OPEN and #13 blocked.

### Initial r8 review finding and source response (not final-zero acceptance)

The requested one bounded independent Standards/Spec pair reviewed initial r8 TREE73c4afbcbf324603d6aef87d0acd47be2932758c: Standards PASS/0; Spec one P2, NOT PASS. Default getattr swallowed an owned extension accessor's AttributeError as absence; a source replay showed native_fixture_pass could remain true and cleanup could destroy the holder. Original candidate/review/native evidence remain immutable. Parent reproduced the exact native_fixture_pass red before correcting; it is not a new Action runtime failure.

Correction stays in the same harness/tests/HANDOFF scope: inspect COMP.extensions, the documented direct list of local attached objects, before named lookup. The fixed source Python class identifier RotoPythonExt selects controller objects (not ownership/display labels). A candidate must be a COMP with that actual attached instance, named lookup must return the identical local instance, and extension.ownerComp must equal the actual node handle before Disconnect/host disable. Empty/non-controller local slots and inherited-only nodes are skipped without ancestor lookup; known local controller lookup has no default, so AttributeError, unreadable direct inventory, owner accessor errors and inconsistent local/named resolution are captured and block finish/cleanup. Node names/paths are only evidence labels. No runtime/backend/Inspector/owner/ACK/builders or artifact/finish/cleanup checks changed.

Expanded exact-seam source regression tests both named/direct owned AttributeError and mismatched inherited resolution, retaining enabled failed host/holder and false native_fixture_pass with cleanup refused. Original r7 inheritance and initial r8 swallowed-AttributeError functions loaded in memory remain red; corrected13 lifecycle/runtime315/Inspector223 are green, source-only. This response/new frozen candidate has NOT received a follow-up independent review: the authorized one pair is completed, its Spec P2 is preserved rather than relabelled PASS. Root must accept the response/read-only review or explicitly authorize a new review round before final-zero native-eligible pin; no duplicate review was launched and no native resume is implied.

### Root owner-mismatch P2 and explicitly authorized round 2

Root read-only rejected response TREEc71849a142e0e01bf1d8ba23de0315c0b2cf6655 as not accepted/native-eligible: actual local attached RotoPythonExt and named instance identity matched, but ownerComp != node silently skipped quiesce. Root RED and parent repeated replay both show quiesce_errors=[], native_fixture_pass=true, local Disconnect calls0, host connected=true, cleanup allowed/holder destroyed. The c718 response, original pair Standards0/SpecP2, both P2 repros and all earlier native/source history remain immutable/unreclassified. No TD/runtime regression was inferred from the source proof.

Minimal harness fix turns known local controller owner mismatch into an explicit captured error before any Disconnect or host write. Genuinely absent/inherited empty-local/non-controller nodes remain skipped; unreadable direct/named inventory, mismatched named/local instance, owner accessor/Disconnect/host-disable/callback-stop errors still fail closed. No ancestor/external controller is disconnected to work around inconsistent local ownership. New capture/evidence/cleanup regression and expanded actual source finish test retain failed holder/artifact hashes/native errors and enforce strict failure. Existing finish/cleanup assertions/retention checks remain unchanged; all17 other feature files/runtime/backend/Inspector/owner/ACK/builders stay byte-identical r7.

Original c718 helper replay remains red; corrected14 lifecycle/full runtime316/Inspector223 source tests pass. Parent uses fake TD ownership/DAT/parameter/disk boundaries only; actual native_local_quiesce/inactive/lifecycle/physical remain held. Root explicitly authorized ONE new independent Standards+Spec follow-up pair (round2) on initial review TREE73c4afbcbf324603d6aef87d0acd47be2932758c→corrected candidate, with full r7 three-file scope and both P2s/retention/native qualifications carried forward. New distinct delegate IDs, no original child-thread continuation, no further rounds without explicit instruction. Final source acceptance requires both axes zero and exact frozen pin/root verification; no edits after review, native resume still needs restored checkpoint and explicit sole Inspector start. #12 OPEN/#13 blocked/#11physicalheld; no own TD/import/install/Connect/otherworktree/commit/push/close.

## Owned Inspector packaging candidate

Local uncommitted composition: Actions 55ef, Follow v5 81ea, migration d588; no #13.
Connection Open Inspector shows a controller-local Fold view. Builder/upgrade and
generic export own and sanitize nested model/views, preserving headless catalog
publication. Live project was read-only scouted; no destructive install yet.
Archive current project and exact old Inspector tox before the separately scoped
native install/Open/reload/two-instance/generic/network-cleanup window.

## #13 current-slot Snapshot implementation (2026-10-09)

Root's accepted #12 CLOSED release supersedes historical blocked statements above. Exact dependency is common commit61d0e03 plus approved TREE55ef1a5febecb6c4f2428e49e899e15d5c030fd8, scopedly applied in issue-13 only with all20 hashes verified; no feature commit. User explicitly requests saved Knob values to follow **current mapping** after remapping (Brightness→Blur). Snapshot now stores normalized slot positions scoped to saved Device/current page, reusing current Binding conversion/readiness/write and #12 Action authority/results/feedback. There is no durable target-key registry/Relink/custom Snapshot hook. Save/overwrite/delete/reload/export are JSON-only; mapping definitions and true COMP/CUSTOM shared values remain independent. Inspector uses existing menu/native dialogs and stale intent guards. Contract [snapshots.md](docs/functions/snapshots.md), source/recovery brief [issue-13-snapshot-brief.md](docs/plans/issue-13-snapshot-brief.md), short direct coordinated gates [issue-13-native-request.md](docs/plans/issue-13-native-request.md).

Superseded parameter-target code/tests/brief and every prior pin remain retained, not silently reclassified. New source synthetic tests cover current-slot remap/range/Menu behavior, immediate reload usability without hooks, shared true values and invariant definitions, honest partial readback and Host feedback, Button guards/repair/ACK zero recall, corrupt storage and generic sanitization. Full source suites/review/exact immutable candidate evidence are delivered separately. Native TD/save-load/export/physical remain pending until Root's sole-Inspector execution; no own live TD/source install/Connect/project/MIDI mutation, canonical saves, other worktree edits, feature commit/push/close.

### #13 r1 review response

Standards r1 zero; Spec r1 two P2 findings preserved on TREE19ae9df: default capture/overwrite lacked tokens for other captured Knobs, and Button value capture conflicted with Root's explicit Knobs1–8-only clarification. Scoped response freezes all implicit capture slot tokens/membership, rejects Button capture at API/store/Inspector, visibly labels current Device/page and0–1 positions, and preflights touch release. Details-only results/values still preserve tokens. New response checks and immutable pin delivered to Root; no duplicate review pair or claimed revised independent-zero acceptance. Shared #10 pending FollowCOMP UI bytes untouched: composition overlaps commands/live_model/ui only, no #13 build_activation edit.

### #13 accepted response composed with #10 Follow v4

Root exact-response adjudication accepted Snapshot TREE51a83 with three focused green regressions and manifest/patch/tree/index verification. Original independent r1 Standards0/Spec2 P2 remain immutable history; this is separate Root source closure. Root authorized source-only composition with accepted Follow COMP v4 TREE7e12cb6d8bbe33cf9d4b93c1dc0075107d657d5e (source Standards/Spec PASS; native UI/physical not inferred accepted).

All18 accepted Follow feature paths composed over exact51a83 via checked scoped patch/temporary three-way files/index; only commands method-insertion anchor conflicted, keeping both blocks. Shared overlaps commands/live_model/ui, Follow build_activation/header/native setter retained exact, no whole-file overwrite of either feature and no backend modifications. Five new interop tests execute actual shared command/observer/UI/builder logic on fake TD: preference toggle independent Snapshot selection/BROWSE/draft; routing/session stale Snapshot dialogs rejected; value/details-only tokens stable; Snapshot menu/save/delete never write Follow or auto Recall; both controls present. Initial fixture missing `_editors` failed strict subscriber-error checks, corrected fixture then green; no runtime/source checks weakened. Required new full suites and immutable composed tree/archive/manifests delivered to Root, main Snapshot delta versus accepted Follow7e12 plus composition delta versus accepted Snapshot51a83. No new independent pair, #11 migration, own feature commit/push/close or shared TD/Connect/project/physical changes. Native queue remains Root sole-Inspector #10→#11→#13.

Composed changed-source checks: full runtime366 / Inspector243 PASS (including5 meaningful Snapshot/Follow interop regressions), synthetic only; current tree/newfiles diff, syntax and Markdown checks bundled. Preservation proof checks Follow15 non-overlap files and Snapshot core bytes exact, shared exclusive methods exact and combined initializer equal to precisely both additions once with base order retained. No duplicate independent review; Root receives immutable complete Git-tree archive and bounded composition diff for parent inspection. Native/save-load/export/physical acceptance and feature delivery remain pending.

### #13 composition with accepted automatic Follow v5 policy

Root's bounded exact parent adjudication accepted r3 TREE5da574 (source only); its full366/243 evidence, original independent review findings and earlier pins remain unchanged. Root authorized exact11-file v4→v5 policy TREE81ea0aca281650515b9f98ae40ff2b6502a6318b / patch1b65d4a9a04e8b97f957841715d72eea0e102938073580405f95dbef0495e03e. Outside-pin v5 final Standards0/Spec0 source review verified. New user authority removes automatic TD Follow TOUCH routing deferral only; prior touch-policy observations/history are not reclassified or diagnosed. Snapshot and manual/hardware/editing touch guards remain.

Checked hunks apply over own exactr3, no conflict/whole-file overwrite/real-index staging. Ten policy files exactv5; only Roto BindControls changes, exact acceptedv5 method; all other Roto/Snapshot methods/core/shared UI and Follow button builder exactr3. One bounded new shared-source/fake-TD interop test proves Snapshot capture/overwrite/preflight/Recall remain touch-blocked while automatic Follow commits, preserves manager touch/freshACK, never implicitly writes targets/Pulse/Recall, and a touched new destination remains Snapshot-blocked. No independent review pair/framework/native rehearsal. New exact fullsource archive/patch/hash manifest and required changed-source checks go to Root for bounded composition inspection. Final #10 restoration→#11→#13 native queue held; no #11 source, own native/Connect/MIDI/canonical/feature commit/push/close.

### #13 on merged owned Inspector / closed #11 — 2026-10-10

Root authorizes source-only composition against merged fork main d7888fe548ffc63a654722adfbb26860255ff3e8, using accepted Snapshot r4 TREE27ebd30 feature delta relative to accepted Follow v5 TREE81ea. Own binding/r4 bytes/index verified first; scoped temporary-index three-way merge preserves main owned Inspector/headless/local lifecycle, controls/layouts/Follow/migration. Code hunks merge clean; CONTEXT/HANDOFF append conflicts retain both complete histories. No whole-directory replacement/reset/clean/staging/other-worktree mutation, and no old Lister revival.

Required snapshots DAT source parity/flags and strict cleanup source/docs groups added; upgrade_network loads snapshots before extension reinit. Root's final public-mapping adjudication remains Float/Int/Menu Knobs only; Button PUSH/TOGGLE/Pulse/Action capture excluded. Internal Snapshot Toggle adapter unchanged, no public Toggle-Knob assignment expansion. Three bounded synthetic seam methods cover packaging parity/classification and actual Snapshot+Action/headless publication/Openinspector/local reconstruction/generic sanitation without parameter writes. Fixture corrections/old review findings remain retained; no new review pair or acceptance relabel.

Final required full runtime/Inspector checks and exact frozen tree/archive/patches/manifest/protected-source record are supplied in the new handoff bundle; main Snapshot delta compares d7888fe, composition delta compares accepted r4. Short direct native request uses the existing owned Inspector/clean Demo; native reopen/export/dialog/current-slot true values/physical/restoration remain pending. Root reviews exact source then explicitly resumes its sole executor. No TD/process/Connect/save/native/physical/commit/push/PR/issue-close operations here.

## Issue #15 source simplification and TouchDesigner file organization (2026-10-10)

Isolated candidate from merged main a035d7386813b3a94bd26f57ab3514c780c6de87; #14 closed without merge. Snapshot intent refreshes native definitions once and validates the full capture set against one fresh model observation. Confirmed commands still refresh again and retain session/owner/selection/revision tokens. Clear retains two-click confirmation but removes the UI's duplicate confirmed-click preflight; command authority still rechecks current target/touch/LEARN/session. No protocol, routing, owner identity, mapping or Button dispatch changes. Source scan counts and remaining native limits: [validation plan](docs/plans/validation-simplification.md).

Moved 27 historical Markdown plans/reports into docs/history and updated links/path references; all existing JSON/JSONL evidence, saved toe/tox, executable module/builder paths and original checkout work remain preserved. [File map](docs/index.md) distinguishes active Inspector source under the historical prototypes name from archived development docs. Native frame cost/latency, actual dialogs, save/load/export and physical acceptance are not claimed. No live TD installation, canonical promotion, commit or push.

Source checks: runtime441 / Inspector248 PASS; git diff --check PASS; 89 Markdown links and 27 document moves verified. Native/physical acceptance remains unperformed.

### Issue #15 targeted native validation

User requested TD tests and rejected old main canonical .75 because it still has Lister. Located exact saved owned-Inspector acceptance artifact cleaned_owned_inspector_review.1.toe (SHA4f9bbe4b…), opened TD2025.33230 and verified /roto_clean_demo/roto_python compact owned Inspector, disconnected/no process/errors0. Preserved prior .75 session in a new recovery save; existing canonical .toe files were not replaced.

Candidate built in isolated disconnected fixture using current external source. Real Float/Int/Menu/BIND Snapshot intents show median default8 2.626→0.424ms, explicit8 3.297→0.321ms, explicit1 0.558→0.246ms over12 alternating samples. Save no value writes, stale native definition rejection and value-only confirmation pass. Actual native view Clear has Sync3→2, removes once and rejects duplicate/control-touched second click; touch was controlled runtime injection, not physical hardware. Configured fixture tox save/load restores2 Snapshots and exact source/local references; no generic sanitation or whole-project candidate reload claim.

Both own fixture roots quiesced/removed; original main executable source/registry/catalog/no-process state exact, compact Inspector reopened and pane at /roto_clean_demo, errors0. One harness DAT-name mistake retained, fixed without product source edits. Native evidence/artifacts in diagnostics/validation/native_results; old .75 and owned-main recovery copies in worktree native-recovery. Original main source still lacks #13; tested candidate was not installed there. No physical/MIDI test, canonical promotion, commit or push.

### Issue #15 actual physical acceptance — 2026-10-11

User explicitly requested physical controller testing. Verified final owned Inspector
project; main was already connected with actual RX but empty current page mappings.
Saved main-before-hardware recovery and raw registry/configuration, disconnected,
installed candidate via external upgrade_layouts (adds merged Snapshot runtime),
verified embedded source hashes and all three Layout IDs, then reconnected.

Actual hardware Knob1 Amount LEARN/input, software0.75 motor/LCD follow, Snapshot
Save no-write and Recall0.00415 verified. Empty Button8 temporarily mapped Snapshot,
actual CC191 27 127 recalled0.65→0.00415 with user motor/LCD confirmation. Actual
view two-click Clear Sync2 removed Button8; reconnect retained Knob1 ACK, subsequent
physical Button8 press had no Recall and Amount stayed0.6. Rejected0/errors0.
Targeted physical acceptance only; no all-slot, physical between-click touch guard,
whole-frame or end-to-end latency claim. Evidence and configured artifacts under
diagnostics/validation/hardware_results/20261011_114002; HARDWARE_TEST.md records
limits and harmless harness corrections. Original canonical binaries unchanged.
Main connected, Knob1→Amount0.6/test Snapshot retained, Button8 cleared. No commit/push.

### Issue #15 executable folder organization — 2026-10-11

User clarified that historical-doc relocation alone did not organize the folder.
Moved61 actual root Python files:11 external builders/upgrades/export/MIDI scripts
to scripts,15 native verification/probe scripts to diagnostics/runtime,35 runtime
tests to tests/runtime. Required root unittest discover command still discovers441
tests through tests package path setup; Inspector248 tests also pass. All builder
loads, test source roots/import paths and current Markdown links updated. Existing
JSON/JSONL capture paths, saved toe/tox, user mappings and upstream code unchanged.
Root now has no Python files; README/CONTEXT/HANDOFF and saved artifacts stay.

Source relocation manifest records original/current hashes. New live TD disconnected
fixture built via scripts/build_network.py, zero errors, exact embedded MIDI source,
no helper process. Quiesced/exported/removed fixture; connected main source hashes
and connection preserved. No repeat physical batch for unchanged embedded runtime.
Evidence: diagnostics/validation/source_moves.json and folder_builder.json.
Changes remain in isolated /tmp/roto-control-issue15; original checkout work preserved.
No commit/push.

### Project and JSON artifact organization — 2026-10-11

User requested an obvious project entry point and proper JSON placement. Actually
organized both original checkout and isolated candidate. Former root .toe files
now live in projects/archive/legacy; original Backup snapshots in archive/backups.
Root JSON/JSONL moved byte-identically to diagnostics/runtime/results; Inspector
JSON/JSONL moved to diagnostics/inspector/results and historical Inspector tox
to projects/components/inspector. Artifact manifest records old/new paths and hashes.
Existing scoped diagnostics and exports retain their content; all moved hashes pass.

Saved the physically tested owned Inspector candidate through live TD, with recovery,
to projects/current/ROTO-CONTROL.toe in the original checkout and copied the saved
artifact into the candidate. OPEN_PROJECT.md plus README/project index give one entry.
Reopened this exact file in TD; restored Snapshot1 and Amount0.6, reopened compact
Inspector, reconnected actual controller and verified Knob1 ACK/errors0/Rejected0.
TD title retains its internal .1 save counter; the unnumbered file is the entry point.
Embedded runtime carries the tested candidate; original checkout runtime source
remains its prior Git baseline, while #15 source work is in the isolated worktree.
Original source runtime230 tests and candidate441/Inspector248 pass; diff checks pass.
No binary editing, artifact deletion, commit/push or inherited source modifications.

### Builder recheck before push — 2026-10-11

User requested renewed builder verification after folder/artifact moves. Isolated
native fixture found fresh build pending restore overwrote immediate mapping, and
native equal-valued Par comparison suppressed a real destination replacement.
Builder now completes binding initialization before return; assignment compares
owner identity/path+name instead of native numeric equality. New regression red
before/green after, full runtime442/Inspector248 PASS. Temporary bidirectional DAT
sync rewrote source CRLF; disabled that startup sync in three build/upgrade scripts,
restored newline-only changes and passed actual source-before/after byte check.

Fresh build, Layout upgrade with mapping retention, Inspector idempotence, configured
tox save/load/local references/Snapshot restore, generic export/load/empty mappings
and Snapshots/embedded sources all pass. Test roots quiesced/removed, connected main
source/registry/PID preserved. BUILDER_RECHECK.md + builder_recheck evidence record
initial failure, corrections and limits. Current working toe was not upgraded to
these additional source fixes; no physical retest/commit/push.

## Issue #3 source fix — 2026-10-11

Isolated branch `fix/issue-3-learn-transaction`, based on main `7d95455`.
Shared destination identity comparison now covers Assign, Free Learn, Pulse
suppression and single-target callbacks without native Par value equality.
ACK preflight validates current range/Menu signature and non-Menu mode/wire
identity before assignment. Delayed Menu knob/button conversion remains supported.
ACK commit snapshots registration, watcher configuration, manual enable flags,
saved assignments, target table and Layout/off-page library; failures restore
these before invalidating the affected hardware mapping.

450 runtime tests pass, including range drift, equal-valued destinations, mode
drift, injected persistence/publication failures and non-legacy library rollback.
`git diff --check` passes. Software verification only: no live TD source reload,
physical acceptance, canonical artifact save/export, commit, push or issue closure.

### Issue #3 native verification and physical-test readiness

TD 2025.33230 isolated fresh builder passed real equal-valued Par Assign/Free
Learn, range drift rejection, injected late publication failure, native watcher
and target-table/registry/library restoration, and subsequent successful ACK.
Native testing found OP Par.eval() returns None for an empty reference; snapshot
now uses Par.val (the serializable reference string), fixing rollback. 450 tests
and diff checks pass. Native harness/evidence: diagnostics/issue3/.

Installed only binding/free_learn/RotoPythonExt DAT source into active
/roto_clean_demo/roto_python after live component recovery exports. Configuration
comparison preserves IDs, targets, library and assignment fields; reload hydrates
identity/Menu metadata and changes only runtime catalog/revision. Physical MIDI
reconnect recalls demo_A Amount on Knob 1 at 0.6, errors empty. Isolated test root
removed. Recovery and test-ready component exports retained; current project file
not overwritten. Physical #3 acceptance pending; no commit/push.

### Issue #3 physical identity acceptance

User confirmed existing Amount/Knob1 input, LCD and motor feedback normal after
source install. Temporary ISSUE 3 TEST Layout and base_issue3_identity COMP then
verified Alpha baseline. With Alpha/Beta equal at 0, Assign replaced Knob1 with
Beta; user confirmed LEARN/rotation/LCD, native state confirmed Beta mapped and
Alpha unchanged. With both at 0.5277421717634133, physical LEARN + Knob1 touch
followed by an explicit same-value Alpha offer used a distinct identity. After
LEARN exit/rotation, user reported done; ACK confirmed Alpha mapped, Alpha=1,
Beta remained 0.5277421717634133. This accepts same-value Assign and Free Learn
hardware replacement, not physical failure injection or every Menu/button case.

Temporary test Layout/COMP and controller test storage removed. Original mapping
configuration/IDs/libraries and all original demo parameter values preserved;
original Amount mapping recalls on Knob1, connected, errors empty. Native snapshots
and recovery/accepted demo tox exports retained in diagnostics/issue3. Canonical
project/export not replaced; no commit/push or GitHub issue closure.

## Issue #4 state-transition source fix — 2026-10-11

Isolated branch fix/issue-4-state-transitions based on main 7d95455. Unlock now
replaces an unflushed locked hardware Device request with the selected Track,
while preserving newer TD Follow and other pending request ordering. LEARN entry
and exit clear partial CC pairs in both Host and all collection controls; duplicate
LEARN messages do not clear a valid in-progress pair.

446 tests pass: same/split batch LOCK/FUNC/SEL/Unlock, backlog/LEARN/touch guards,
all eight knobs and both partial-pair directions, with old fenced input not writing.
Existing mixed TD/hardware owner Follow ordering passes after constraining Unlock
replacement to pending None or hardware_plugin. Standards/Spec re-review clear;
git diff --check passes.

Native TD 2025.33230 isolated fresh build passes partial-pair rejection, same/split
batch Unlock and locked explicit Device selection. Main MIDI PID retained; fixture
removed. Evidence/harness: diagnostics/issue4. Production live controller retains
issue #3 source; #4 has not been installed there or physically accepted. No #4
commit/push, canonical artifact save/export or GitHub mutation.

### Issue #4 live install and physical selection acceptance

Installed only protocol/collection_protocol/text_comp_follow DAT source into the
active controller; retained issue #3 source. Recovery demo tox retained locally.
Physical test in temporary ISSUE 4 TEST Layout: LOCK on, FUNC selects TRACK B,
SEL selects A DEVICE 2 while routing remains TRACK A. Native inspection confirms
LOCK true, selected Track B and routing A Device 2. User then unlocks and confirms
TRACK B / B DEVICE 1; native inspection agrees, no pending/fence/errors.
This accepts physical selector sequence, not proven same-batch hardware arrival or
physical partial-CC injection (those remain software/native synthetic evidence).

Temporary Layout/test storage removed; original IDs/configuration/libraries and
all demo values retained. Amount recalls on Knob1, connected, no errors. Recovery,
accepted demo tox and evidence retained in diagnostics/issue4. Canonical project
not overwritten; no #4 commit/push or issue closure.

## Issue #5 runtime BIND ownership source fix — 2026-10-11

Isolated branch fix/issue-5-bind-ownership, main 7d95455. Current parameter-chain
claims are checked before SetValue, hardware dispatch, feedback callbacks, MIDI
receive, Tick and offers. Overlapping claims (including suspended registrations)
suspend all affected controls with public errors, clear mapping/deferred input,
and withdraw unsent per-control feedback while retaining unrelated/session output.
Semantic validation failure does not hide an otherwise valid chain claim.

448 tests pass: runtime rebind, no hardware/feedback writes, both owners suspended,
unrelated control retained, selective queued feedback removal, narrower-clamp
conflict, valid unclaimed rebind and explicit re-registration recovery. Existing
cycle/missing/readonly/EXPRESSION/EXPORT checks remain. Native TD 2025.33230 verifies
real BIND chains, blockade, unaffected control, preserved expressions, recovery,
unclaimed rebind and synthetic hardware no feedback; main MIDI PID retained and
fixture removed. Harness/results: diagnostics/issue5. Standards/Spec review performed.

Physical acceptance pending. Main live controller retains #3/#4 code, not #5.
No #5 commit/push or canonical project/export replacement.

### Issue #5 integrated live install and physical acceptance

Composed #5 extension changes over #3 and retained #4 protocol/arbiter sources in
a temporary integration bundle; combined 460 tests pass. Installed controls and
composed extension DATs after live recovery export; original configuration retained.

In temporary ISSUE 5 TEST Layout, user LEARNed three explicit BIND aliases via
Offerparameter and confirmed each knob changes only its own master. Runtime
Aliastwo rebind to Masterone produces ownership errors on Knob1/2; both suspend,
user rotation leaves Masterone/Mastertwo unchanged while Knob3 changes Masterthree.
Restoring reference alone retains suspension. Apply setup recalls all three
mappings without re-LEARN; user rotates Knob1/2, native inspection confirms both
masters changed independently and unrelated Masterthree remained unchanged.

Temporary Layout/COMP/test storage removed; original mapping configuration, IDs,
libraries and all original demo values retained. Amount recalls on Knob1, connected,
errors empty. Evidence and recovery/accepted demo exports retained locally in
diagnostics/issue5. Canonical toe/tox not replaced. No #5 commit/push or issue closure.

## Automatic parameter-page hint — 2026-10-17

Parameter mapping now uses the main Menu Window's lower name field for a brief
TD parameter-page hint, restoring the real Track name after two seconds on the
next safe Tick. Only acknowledged matching slots contribute. Different pages or
COMPs, callback/action targets, invalid targets and empty mappings use the Track
name. Existing LEARN/touch/LOCK/restore/context/backlog guards and queue fences
remain in force. No new timer, UI setting, Screen 8 output or routing policy.

Runtime changes are confined to RotoPythonExt, controls and layouts. Nine new
regressions cover expiry/deduplication, native page metadata, matching/rejected ACKs
and partial readiness, ambiguous/invalid/callback targets, empty/same-name recall,
guards, session/selection replay and existing fence cancellation. Full source
discovery passes 478 tests on this PR's 9f02879 baseline. Its runtime before the
caption delta matches the physically tested saved source 2de08c9; the intervening
main changes affect validation documentation only.

On TD 2025.33230, firmware 3.3.0 / API 1.6, the user confirmed COMP Follow
demo_A to demo_B and back: each main screen shows Demo then EFFECT, with normal
control screens. A hardware right/left arrow-page round trip recalls the original
three knobs and replays the hint. Native output intervals were about 2.00–2.30
seconds. Earlier manual Demo/Controls caption checks passed three round trips;
FUNC's list retained EFFECT. Exact guarded/mixed-target physical rendering, new
LEARN behavior and the initial-connection Track-line refresh are not accepted by
these observations.

Restored the original four control definitions/IDs, registry except monotonic
revision 221, controller parameters, linked-COMP values/modes, Snapshots, Follow,
LOCK and original context. TD remains open/disconnected; temporary observers were
removed and scoped native errors are zero. The existing ordinary connection
stale/Menu reconciliation limitations were observed, not changed.

Local candidate project and generic export were saved through TD after retaining
recovery copies. That generic tox reloaded empty/disconnected with no user mappings,
ownership/Focus links or Snapshots, embedded helper/docs and Python=python3.
Its principal runtime hashes match the tested source. Remote canonical artifacts
predate the current source and are intentionally unchanged by this source-only PR;
artifact synchronization is separate. Layout documentation retains current-main
ownership and Follow policy; the caption section alone was added, and the local
candidate snapshot was refreshed.

One-off native evidence and original recovery remain local, not in this PR:
system temporary roto-page-feedback-m_1qjypu and
projects/archive/page-caption-20261017-recovery. No hardware learned-storage
readback or full main-project restart is claimed. These caption observations do
not establish physical LEARN/ACK acceptance for the metadata refactor below.

## LEARN metadata integration — 2026-10-17

Integrated the scoped LEARN refactor over caption source `e6a5c2f` in the same
PR, preserving current ownership/transaction code and page-caption behavior.
Immutable `LearnParameter` and the pure `learn_parameter_message` encoder serve
registered controls, Free LEARN and the legacy Host. Menu labels pass explicitly
through Controls specs and replacement-Control paths. Formatter introspection
and the temporary session-enabled Control are removed; index/hash/Menu
signatures, multiple pending offers, matching ACK handling, routing and target
writes keep their established paths.

The combined source passes 481 tests through `python3 -m unittest discover -q`
from `src/touchdesigner`. Three added regressions cover formatter-independent
Menu metadata, the 16-label boundary and Free LEARN/registered packet parity
without parameter or Pulse writes. A previously captured corpus of 163 complete
LEARN messages matches before/after byte for byte.

Earlier native TD integration captured packets from four actual registered
controls and four isolated FreeLearner offers against the same native parameters.
All eight packets match before/after; callbacks were restored immediately and
the isolated learner made no real Inspector/status or session writes. Imports
share the same LearnParameter class. Native reload preserved all four original
definitions/IDs, registry revision 221, controller parameters, linked-COMP
values/modes and Snapshots; scoped errors were zero. Generic tox reloaded empty
and disconnected with no user mappings, Focus/ownership links or Snapshots,
embedded helper/docs and Python=python3. This is native encoding/import/reload
evidence, not a new physical LEARN/ACK or full project-restart acceptance.

Local project/tox were saved through TD, with recovery retained in
`projects/archive/learn-metadata-20261017-recovery`. The local receipt records
caption source e6a5c2f plus the reproducible LEARN patch and the eight principal
runtime hashes, which match this combined PR source. Checked-in binaries and
their older receipt remain unchanged; this PR publishes the source/tests/docs
for both changes. No TD/controller operation was needed to package the PR.

One-off packet captures, native probes and save/export results remain in the
system temporary directory `roto-learn-integration-r84fm_j_`, including
`packets-before.json`, `packets-after.json`, `native-packets-before.json`,
`native-packets-after.json`, `candidate-native.json`,
`generic-export-validation.json` and `save-result.json`. No MIDI connection,
hardware LEARN, parameter/Pulse write or new hardware acceptance was invoked
by the metadata integration.

## Generic export sync — 2026-10-17

The user selected generic tox and version receipt synchronization, leaving the
demo toe out of scope. Verified the active project, then compared the intended
`/roto_clean_demo/roto_python` with PR source `0ed7d97`. All 19 present
runtime/helper DATs match; the four absent files are legacy outer-Control/Lister
callbacks outside the owned export. The project also contains an older controller
at `/roto_control_python/roto_python`; it was observed only and not upgraded.

Loaded the local generic tox in an isolated root fixture. All 19 embedded
runtime/helper sources match the combined PR. Its embedded README was older;
refreshed source Markdown on the detached clone and exported through live TD,
then reloaded the resulting artifact. All 19 source hashes and ten documentation
snapshots match the recorded source commit. The export is empty/disconnected,
Follow off, Python=python3, with embedded helper, no DAT file dependencies,
no user mappings, Focus/ownership links or Snapshots, and zero scoped errors.
The fixture was quiesced and removed; original controller storage, runtime
sources and linked demo parameter values/modes are unchanged. No hardware/MIDI
operation or new physical acceptance was performed.

Promoted only `exports/roto_python.tox` and its adjacent `roto_python.json`
receipt, plus the export index/current-context documentation. The receipt pins
runtime/documentation source to `0ed7d975d17a50c193c134cffac97ea63a6ea976` and
artifact SHA-256
`509911ddcb0d23db9c8db3aa4706140c1475cb64dad4bcd975d659aff125515d`.
The 481-test source result is reused because runtime sources did not change.
The demo toe and its checked-in project receipt remain unchanged.

Recovery of the prior local tox/project receipt is retained locally under
`projects/archive/generic-export-20261017-jh0ke_d6`; the prior checked-in tox,
one-off native script and validation result remain in system temporary
`roto-generic-sync-4hp7mefd`. Local working-project receipt now points to the
updated generic export receipt without changing the demo toe bytes.

## Track group palette colors — 2026-10-17

Implemented on `feat/td-track-colors`, based on `acc7a5c`, separately from
PR #23. Changes are uncommitted. `layouts.py` persists optional Track palette
indices 0..82 and includes them in existing Track details/selection messages.
`RotoPythonExt.py` exposes `SetTrackColor` and `GetTracks().color`; `setup.py`
adds the Layout-page Track color menu. Omitted colors retain palette 0 without
registry migration. No arbitrary RGB, transport rewrite or queue adapter was
added. Official SysEx v1.6 Appendix A identifies the palette; index 47 has a
non-hex component in that table, so its menu entry retains only its identity.

The final source passes 486 tests through `python3 -m unittest discover -q`
from `src/touchdesigner`; the scoped Layout suite passes 26. Five new tests
cover persistence, API/UI edits, packet colors, offline replay, connected edits
to another Track without selecting it, reset-to-default, invalid inputs and
LOCK/LEARN/touch/routing guards. Existing wrong-target, stale-ACK, persistence
and exactly-once coverage remains. `git diff --check` passes.

Native TD 2025.33230 checks exercised the actual menu and Track selection
callbacks across frames, rejected a locked color edit and restored its UI,
then saved/reloaded configured colors 71/82. The generic candidate reloaded
empty/disconnected, with 83 menu choices, Layout 11 fields, Device 6 fields,
default color 0, Follow off, Python=python3, no user mappings, Focus/ownership
links or Snapshots, 19 matching runtime/helper DATs and zero scoped errors.
The isolated fixture was quiesced and removed.

Installed only the three changed DATs in the receipt-designated live controller
`/roto_clean_demo/roto_python`, after retaining its configured tox, all 19
original sources and registry/parameter/value evidence. The separate old
controller was not upgraded. Physical PLUGIN acceptance used temporary EFFECT
palette 71 red and COLOR TEST palette 82 purple. The user confirmed both have
white text in FUNC; selecting the second hardware button showed
`CUSTOM / COLOR TEST` in purple, and returning showed `demo_A / EFFECT` in red
with the original Knob 1–3 screens normal. No knob rotation or LEARN was
requested. Arbitrary RGB and all 83 physical colors remain untested.

Restoration removed the temporary Track/colors and disconnected the MIDI child.
Original registry definitions, four control IDs, controller parameters, Follow,
LOCK and Snapshots are preserved; revision advances from 221 to 236. Before
restoration, demo_A.Amount differed from 0.4 to 0.44924616981016907. The user
confirmed manually changing it during testing. Preserved that value and modes;
the restored catalog's value/normalized cache reflects it. Do not claim unchanged parameter values for
the whole physical session. The normal connection also reported the existing
stale/Menu reconciliation warning; hardware learned-storage was not read back.

The active project remains unsaved with the candidate runtime. Canonical demo
toe, generic tox/receipts, PR #23 and original dirty-checkout sources are
unchanged by this feature. No commit, push or PR publication was performed.
The restored configured candidate was saved through TD as
`restored-track-color-candidate.tox` in system temporary
`roto-track-color-sgtyqd5s`; generic `roto_python.track-colors.tox` there has
SHA-256 `d56ea7cea4b721012c8ef4bcf159c4783661f2d3046b922e1b6b5067c7948cb1`.
These are candidate/recovery files, not the canonical export. One-off evidence
includes `native-validation.json`, `physical-test.json`, `restoration.json`,
`target-value-differences.json` and the pre-test configured tox/source snapshots.

## Track color save and export — 2026-10-17

Saved the accepted Track palette feature through live TD after the user requested
the next step. The active project and 19 runtime/helper source hashes matched
`acc7a5c` plus the uncommitted feature. Original four control IDs, registry,
controller parameters, Follow, LOCK, Snapshots and current linked-COMP values/modes
are preserved. Amount remains the user's manually edited 0.44924616981016907.
The separate old controller was fingerprinted and remains unchanged.

Refreshed ten Markdown snapshots from the feature worktree, exported the generic
tox through TD, then reloaded it. It has 83 color choices with default 0, Layout
11 fields and Device 6 fields, empty mappings/Focus/ownership/Snapshots, Follow
off, Python=python3, embedded helper, no DAT file dependencies and zero scoped
errors. All 19 runtime/helper and ten documentation hashes match the feature
source. The temporary export fixture was quiesced and removed before saving.
No new hardware operation or full main-project restart was performed. Reuse the
same-candidate 486 source tests and prior physical red/purple A/B/A acceptance.

TD saved `ROTO-CONTROL.track-colors.20261018.toe` in the original project's current
folder; the numeric suffix is TD's incrementing save counter. Promoted its bytes
to local canonical `ROTO-CONTROL.toe`, SHA-256
`030e2fee006ea9b3e77a8c00fecf65f0cb9ff4625386884f6e3c372476b46ade`.
Updated the local project receipt and both local/feature-worktree generic tox
and receipts. Generic SHA-256 is
`b28b0f3ba3d045d7c6f58d286052dc92e303bd3c44aaea869ab9b538d56d1fe0`.
Receipts identify source base `acc7a5cb7fbba234dc2cef80fcf880c19c3d5a99` plus
`upgrade/track_colors_acc7a5c.patch`, SHA-256
`aa3ede4893dee6ead9809ef6d9cb7708f7419bc216ecae92b13839fd9dd55133`.
The reproducible patch includes three runtime files, Layout docs, regression
tests and the affected existing native verifier count. It excludes artifact and
receipt bookkeeping; content hashes identify the actual embedded runtime/docs.

Recovery is retained in the original checkout under
`projects/archive/track-colors-20261017-iiqv8cgr`, including prior canonical
artifacts/receipts and the configured live controller before doc refresh.
One-off scripts/results are in system temporary `roto-track-color-save-a5_opi_s`,
including `live-baseline.json`, `save-result.json` and `promoted.json`.
The open TD project remains saved/disconnected with no MIDI child. This save
supersedes the earlier unsaved-candidate note. This feature remains uncommitted;
PR #23 and its clean worktree were not changed. The feature worktree's checked-in
demo toe/receipt retain their independent older version; only its generic export
was synchronized. The original dirty checkout's runtime sources remain intact.

## Track color BG preview — 2026-10-17

Added a native read-only RGB custom parameter, `Track BG preview`, beside
`Track color` on Layout. Three reactive expressions derive normalized RGB from
the existing palette labels through a pure setup helper. No preview callback,
queue or MIDI message was added. The menu remains the sole color-setting input;
preview components cannot be edited in TD's UI. Index 47's invalid `81 BO 4A`
appears in both official SysEx v1.6 Appendix A page 33 and Serial v1.3 Appendix A
page 27. Its preview is explicitly unavailable/disabled, with correction tracked
in https://github.com/joshuahhn/roto_control/issues/24. It remains selectable as
a hardware palette index.

Source passes 487 tests, including a palette-to-normalized-RGB regression for
default/red/purple, invalid indices and unavailable 47. Native TD checks pass
for actual menu callbacks, red/purple Track switching, read-only/expression flags,
unavailable 47, repeated setup and configured tox reload. Layout now has 14
component fields, including the RGB triplet; Device remains 6. Original registry
definitions, source DATs and demo values were preserved during isolated checks;
only the monotonic registry revision advanced from 236 to 238. The fixture was
quiesced and removed. Physical color acceptance from the unchanged packet path
is reused; preview checks did not open MIDI.

Installed only the updated setup DAT in the intended live controller, preserving
all four control IDs, original controller parameter values, registry definitions,
Snapshots and target values/modes. Saved through TD as
`ROTO-CONTROL.track-preview.2.toe`, then synchronized local canonical toe and
root/feature-worktree generic tox with receipts. Generic reload is empty and
disconnected, default palette 0 and its read-only preview, Follow off, embedded
helper, Python=python3, no external DAT files or mappings/ownership/Focus/Snapshots,
19 matching runtime/helper hashes, ten Markdown hashes and zero scoped errors.
No full main-project restart is claimed.

Local project SHA-256:
`68420323eeddd934027da07794c9d603acaffe68af4a8ce8176798861df73bdd`.
Generic tox SHA-256:
`97f03362bc89ae6964a84150fc995f2cddca58589b981e7ed4859791e22f6a50`.
The updated reproducible patch over `acc7a5c` includes runtime, Layout docs, both
regression files and the affected verifier; SHA-256:
`4ca208affd1267560221023f202d0f3027b12b1cc7c6573fb378c39b846d38f6`.
Recovery is retained in original checkout
`projects/archive/track-color-preview-20261017-kihi1uoh`; one-off native/install/
save/promotion evidence is in system temporary `roto-color-preview-da2187d6`.
The open TD project remains saved/disconnected, current Amount is preserved,
and the old controller is unchanged. This supersedes the earlier artifact hashes.
The feature worktree's generic export is updated; its checked-in demo toe and
receipt retain their independent older version. PR #23 was already merged on
GitHub when checked; it was not merged by this work.

## Track color source and generic publication — 2026-10-17

Committed Track color, read-only background preview, regression tests and scoped
native evidence as `0254000d1f3810fea47713043c8951f6f1d098ee`. Generic receipts
now pin all 19 runtime/helper and ten embedded documentation hashes to that
commit, replacing the temporary base-plus-patch description. The source patch
is retained in local recovery rather than duplicated in the published source.
The generic tox keeps SHA-256
`97f03362bc89ae6964a84150fc995f2cddca58589b981e7ed4859791e22f6a50`.
The local canonical project receipt also identifies the same committed source;
its saved bytes and current values were not changed while packaging publication.
Checked-in demo project/receipt retain their separate earlier baseline.
The 487 source tests and scoped preview/native/export/physical evidence above
are reused, because publication does not alter runtime or UI behavior.


## Actual Kick output acceptance and MIX configuration decision — 2026-10-17

On user instruction, extended the bounded one-knob probe to temporarily enable
`audioAnalysis.Kickactive`. Its bound child `kick.Active` selected
`null_kickSignal` through `switch1` into `Kickdrum`; the public output was
`out1['kick']`. Trigger peak length was 0.1 seconds. Hardware K1 was derived
only from observed real output, with a 0.2-second display hold; it was not
inferred from a level/threshold comparison. Eight temporary input/indicator
tests passed. User confirmed K0/K1 alternation, T.262 and normal native meters.

The high-threshold control set Kickthresh to 0.600 temporarily. User still saw
K1. Native records explain this correctly: pre-threshold level reached
0.61..0.70, with positive `math8` difference, gate=1 and actual kick output=1.
There were 63 observed pulse rises in that high phase after settling, and
367 in the full bounded probe. This was not a valid no-trigger condition.
Meter scaling at 0..0.6 clipped these peaks; production meter range must be
independent of the control range. Threshold subtraction matched level minus
threshold within 5.37e-8. One comparison of upstream Kickdrum versus public
out1 differed within the first 187 samples after enable, with no further
mismatch through the final 6552 samples; display authority remained out1.
This records an initialization/read-timing limit, not a palette defect claim.

The bounded timeout restored both the agent's temporary threshold and Kickactive.
User confirmed normal PLUGIN return, then Disconnect closed/reaped the child.
Final audit preserves Kickthresh=0.26174693279619116, Kickactive=False,
Audioout=False, all parent writable audioAnalysis parameters and child binding
modes/expressions, controller parameters, demo_A/B values, Snapshots, four
original local control IDs and 19 source/helper hashes. Registry definitions
match baseline except revision 271 to 283. Temporary receiver/probe and pending
output are gone. Scoped native checks for the controller, Kickdrum, trigger1
and out1 returned no errors/warnings. No saved toe/tox or production source
changed. Scripts, recovery and detailed results are in system temporary
`roto-kick-trigger-_axhupqr`; this is a one-off acceptance probe.

User explicitly selected the production design: an independent MIX page with
eight slots, each configured with its own control target and meter source.
It must not reuse/switch with the current Device's PLUGIN assignments.
Implement MIX All Tracks/Level first; preserve PLUGIN routing/LEARN, existing
transport, session/epoch fences and value/motor ownership. AudioAnalysis and
later Layer Mix opacity are the concrete uses. Meter range is separate from
control range, and native yellow/red thresholds are global across MIX meters.
The production adapter, saved configuration/UI, source/native/physical checks,
generic tox/receipts and PR remain work to do. Root checkout stays dirty and
its existing edits must be preserved; PR #25 was found already merged on GitHub
at 2026-10-16T18:55:15Z, not merged by this work.


## Low MIX Focus prototype and deferred audio issue — 2026-10-17

User explicitly deferred audio refinement and authorized a future issue:
[issue #26](https://github.com/joshuahhn/roto_control/issues/26), labelled
enhancement/needs-triage, records explicit Gain/Mute destinations, meter stage and
retained Gain on unmute. No audio processing stage was built. Analysis remains
the first production style.

Active project remained `ROTO-CONTROL.track-preview.2.toe` and the correct
controller `/roto_clean_demo/roto_python`. A temporary receiver and the existing
external MIDI owner provided one MIX item, Low, with two named Sends for Add and
Smooth. Actual All Tracks readback was `0C 01 00 00 00 00`; FUNC reported
`0C 02 00`. Target ranges came from native normalization: Threshold 0..0.6,
Gain 0..7, Add -1..1, Smooth 0..1. The meter used public `out1['low']` at 10 Hz
over 0..1, labelled as processed output rather than threshold input.

The initial display-only phase made zero parameter writes. User observed
`MIX-FOCUS / Low`, `Thresh 0.100`, `Gain 2.000`, `Add 0.000`, `Smooth 0.000`,
an underscore/lower-line display and continuing first-screen meters. This
establishes readable combined name/value text via SHOW CONTROL VALUE; it does
not establish arbitrary replacement of every firmware heading.

Only a new Knob 2 touch could then write Lowgain. CC13/45 pairing accepted both
orders, rejected stale halves and cleared on release. User reached displayed
Gain 2.841, native value 2.84093267411341. There were 66 changed writes during
the gesture, with Threshold/Add/Smooth unchanged. Input was then removed again,
Gain was explicitly restored to its original 2.000, and no additional input
writes occurred during hands-off feedback.

The 60-second reset observation expired before the user's text report. The
original probe cleanup republished PLUGIN Track metadata while hardware remained
MIX Focus, producing native VOLUME/PAN/SEND A/SEND B and EFFECT. This was a
test-method cleanup defect. A temporary regression at the actual finish method
failed, then passed after deferring metadata restoration until actual PLUGIN
return. A second test covers ordering that restoration after the PLUGIN message.
A fresh three-minute read-only phase passed physical four-text, Knob 2 at about
29%, and continuing-meter checks. User then confirmed normal PLUGIN. No production
framing defect or general firmware-label defect is claimed.

Final cleanup closed/reaped the child with return code 0, removed the receiver
override/probe and left zero pending bytes. Disconnected restore reinstated local
definitions, not a readback claim about hardware learned storage. Registry data
match baseline except revision 283 to 290. Controller parameters, all parent
writable analysis parameters, child Kick bindings/modes, demo_A/B values,
Snapshots, four original IDs and all 19 runtime/helper hashes match baseline.
Kickthresh remains 0.26174693279619116; Kickactive and Audioout remain off.

Twelve temporary decoder/projection/cleanup tests passed; they are one-off probe
tests, not a production runtime suite. Scoped native checks for the controller
and analysis out1 returned zero errors/warnings. Recovery tox, scripts and separate
display/input/final results remain only in system temporary `roto-low-details-xmewaxym`.
No canonical toe/tox, embedded DAT source or runtime module changed; no commit or
PR was created. The project stays open and disconnected. Source integration of
the shared descriptor and Low/Mid analysis routing is the next authorized step,
preserving the dirty checkout in an isolated worktree.

## Independent MIX analysis source slice — 2026-10-17

Implemented in isolated branch `feat/td-mix-analysis`, based on fork main
`faf3bad54ca1fc800ea777ec50326fbbb03fc271`. The original dirty root checkout was
not reset, cleaned or used as runtime source. Preserved only the three approved
new design documents and the two relevant prototype-evidence sections above.
Official integration guidance already matches this checkout.

`mix_descriptor` validates versioned data for exactly layers/analysis/audio and
describes existing Low/Mid parameters. `mix_runtime` enables the analysis float
slice independently of PLUGIN, with overview and first Focus-page projection,
fresh-touch/pair/session fences, explicit target identity/range/mode checks,
deferred motor feedback and independent 10 Hz coalesced meters. The small
`midi_queue` filter preserves in-flight frame tails. Extension dispatch isolates
shared Track metadata/selection as well as CC/ACK business traffic, and restores
PLUGIN metadata only after its actual mode message. No fake PLUGIN mapping, new
MIDI owner or wire protocol was added. Configuration, APIs and current limits
are documented in [MIX analysis](docs/functions/mix.md).

The final runtime source passes `python3 -m unittest discover -q`: 509 tests,
including 22 new MIX tests. Existing wrong-target, stale-ACK, persistence,
ownership, Follow and exactly-once coverage remains. Native TD 2025.33230 fixture
passes eight actual Low/Mid float writes with unrelated targets unchanged,
scalar CHOP metering, saved configuration reload without value recall, repeated
disconnected upgrade, and zero scoped errors. Temporary generic export/reload
from the complete live controller passes empty MIX configuration, no external
DAT files, embedded helpers, disconnected state and zero errors.

The attempted full fresh builder reaches an existing ASCII-locale failure in
Inspector source reads, first `inspector_data.py`, then `parity.py` through nested
builders. A partial UTF-8 repair was withdrawn to avoid expanding this slice.
The scoped `scripts/upgrade_mix.py` is natively accepted and does not rebuild
Inspector. Do not describe the full fresh builder as passing in this environment.
Builder/cleanup source now classifies the three helpers and the new function doc.
The native upgrader also verifies one owned MIX annotation after repeat installs;
Annotate's initializer overrides its requested name, so naming occurs afterward.

Installed only the five affected/new DAT sources in
`/roto_clean_demo/roto_python`, after verifying all 19 baseline hashes against the
existing receipt. Its 22 runtime/helper hashes now match this worktree plus the
unchanged saved baseline. Configured the existing `audioAnalysis` scope for Low
and Mid. All writable analysis values, four original mappings, registry
definitions and Snapshots remain equal, allowing the monotonic registry revision
and serialization-equivalent tuple/list forms. Read-only level/trigger samples
are live measurements, not configuration equality checks. Midactive remains
False, Lowactive True, Kickactive/Audioout False, and the user's Kickthresh remains
0.26174693279619116. The old controller and unsaved audio nodes remain untouched.

One-off recovery, scripts and separate native/install/generic results are in
system temporary `roto-mix-source-34paqmy5`. The temporary fixture was removed.
TD remains open/disconnected, no receiver override, zero pending output and zero
scoped controller errors. No hardware ports were opened by this source slice.
No canonical toe/tox or receipt changed; no commit, PR or merge exists for MIX.

Next is affected physical acceptance of Low/Mid selection, FUNC details, float
input/motor and normal PLUGIN restoration. Active/menu/button/trigger routes,
second-page Focus, Layer Mix, the slot editor and audio #26 remain later slices.
The earlier bounded Low/Gain proof is not acceptance of these new multi-item
routes. Canonical save/export and PR publication follow the scoped hardware check.

## Retained FUNC across MIX and PLUGIN — 2026-10-17

User observed that FUNC remains on across MIX → PLUGIN → MIX. A fresh bounded
connection first reported `0C 01 00 00 00 00`; the user saw MIX-TRACKS, Low/Mid,
KNOBS-VOL, screen-1 metering and FUNC off. Record this separately from a mode
round trip; do not infer retained FUNC behavior from a new DAW session.

Kept the same external MIDI child while renewing the bounded observation window.
User pressed FUNC, PLUGIN, then MIX without pressing FUNC again. The trace records
Focus `0C 02 00`, PLUGIN `0B 01 00`, then direct Focus `0C 02 00`, without an
intervening All Tracks report. Runtime projected Low's first details page and
made zero parameter writes. User confirmed MIX-FOCUS / Low, FUNC on, with native
Volume/Pan/Send A/Send B and four color labels. This accepts retained Focus and
main-screen context; it does not yet accept the four small control screens'
combined text/value rendering after the mode round trip.

Added a real-extension regression for direct Focus return without an overview
message, preserving selected item, values and fresh-touch fencing. It passes on
the existing implementation; no runtime change was needed for FUNC retention.
Full runtime discovery now passes 510 tests; `git diff --check` also passes.
One-off trace, snapshots and observation are in system temporary
`roto-mix-func-retained-6he9wazp`, with the round-trip stage in its `roundtrip`
subdirectory. The 180-second timeout disconnected/reaped the child and removed
the diagnostic trace wrapper; it did not publish PLUGIN metadata over MIX.

The existing hardware/local Button-1 reconciliation difference recurred during
PLUGIN recall. Disconnected restoration reinstated the four original local
control IDs and registry definitions, allowing revision advance. This preserves
local definitions, not a claim about learned storage readback. Analysis/demo
values, MIX profile and Snapshots match baseline. No pending bytes, trace or
receiver override remain; scoped controller errors are zero. No canonical save,
export promotion, commit or PR was made. Next read the small control screens,
then continue affected multi-item routing acceptance.

## MIX control-text expiry correction — 2026-10-17

After the bounded FUNC test had stopped, user read the small screens as
VOLUME/PAN/SEND A/SEND B. Re-read official SysEx API v1.6 section 2.23: SHOW CONTROL
VALUE uses a timeout and returns to the control name without further messages.
The accepted temporary Low probe renewed text every 250 ms. The source slice
instead cached unchanged text indefinitely, which cannot sustain that display.
The request to read the screens after disconnect was also an invalid method for
accepting live combined text. FUNC persistence itself remains accepted.

Added a real-extension output regression for unchanged Focus text renewal,
existing 10 Hz throttling, no repeated motor messages, bounded/coalesced unsent
captions, zero parameter writes and no MIX renewal after PLUGIN return. It failed
with no renewed captions, then passed after renewing assigned text on the bounded
feedback tick. Unassigned blank text still clears only when needed. Full runtime
discovery passes 511 tests.

Installed this correction through the scoped upgrader while disconnected, with
a fresh recovery tox and unchanged registry definitions, writable analysis/demo
values, MIX profile and Snapshots. Native scoped errors are zero. One-off
recovery/install/active-feedback results belong under temporary
`roto-mix-func-retained-6he9wazp/text-renewal`. Active hardware text acceptance is
the next check; no physical success is claimed by this source correction alone.

## MIX Low/Mid hardware acceptance — 2026-10-17

Accepted the production source with the text-renewal correction, on firmware
3.3.0/API 1.6 and TD 2025.33230. User confirmed all four Low captions remain
readable for ten seconds with FUNC on. Touching overview Knob 2 and then FUNC
selects Mid, displaying MIX-FOCUS / Mid and Thresh 0.100, Gain 4.000, Add 0.000,
Smooth 0.100. Selection/viewing made zero parameter writes. Midactive remained
False; its processed-output meter can correctly be zero.

A fresh Knob 2 gesture changed only Midgain from 4.0 to 4.396630653726423,
displayed 4.397, with 21 changed input writes. TD restored 4.000, and the user
confirmed the motor return and all four captions. The return observation was
repeated after the user missed its first movement; no additional input writes
occurred during either hands-off motor move. Original writable analysis values
were restored, including Midgain 4.0, Lowgain 2.0 and the user's Kickthresh
0.26174693279619116. Detection/audio toggles were not enabled.

User then confirmed normal demo_A PLUGIN parameter/value screens. The bounded
diagnostic trace/send wrappers were removed and the single child was closed and
reaped with return code 0. No receiver override or pending output remains.
Disconnected restoration reinstated the four original local IDs after the
existing Button-1 hardware/local recall discrepancy. Registry definitions,
analysis/demo values, MIX profile and Snapshots match baseline, allowing registry
revision advance and unordered needs_relearn serialization. This is local
configuration preservation, not hardware learned-storage readback acceptance.
Scoped controller errors are zero.

Final relevant source discovery passes 511 tests, including 24 MIX tests. Native
eight-float target/conversion, configured reload, repeated scoped upgrade and
generic sanitization evidence above remains applicable. Physical acceptance is
limited to overview metering, touch selection, first FUNC details, Mid Gain
input/motor, retained FUNC and PLUGIN return. Pan/Send overview input, other
physical detail inputs, buttons/menus/triggers and CI=8+ remain unverified or
disabled as documented. Full fresh Inspector construction still has the
separate ASCII-locale limitation; the scoped updater passes.

One-off results remain in system temporary
`roto-mix-func-retained-6he9wazp/text-renewal`, including mid-selection, mid-gain,
mid-gain-final-return, final-plugin-return and final-restoration.json. TD remains
open and disconnected with user audio nodes preserved. The generic save/export
receipt will identify the exact committed source and embedded hashes; the
checked-in demo project/receipt retain their prior independent baseline.

## MIX generic publication — 2026-10-17

Source and the scoped evidence above are committed as
`58ff695a5fef1206ff05aa12ff0a3c5dff625c75`. Refreshed eleven Markdown snapshots
through live TD, exported a generic controller and reloaded it in a temporary
holder. All 22 runtime/helper and eleven documentation hashes match that commit.
Reload is disconnected, Python=python3, Follow off, no external DAT dependencies,
empty MIX profile, mappings, Snapshot records, ownership and Focus links, with
zero scoped errors. Unchanged menu/color/LEARN behavior reuses its prior evidence.
The documentation-only layout check places eleven DATs inside two measured
groups without overlaps. Original outer Guide positions are retained; their
pre-existing overlap with runtime nodes was also present in recovery and was not
expanded into a controller-wide layout change.
The generic SHA-256 is
`a60fc7d2c59cf270b630081ca8f123ef9159c3494a24aa589eae03498c8c6352`;
`exports/roto_python.json` pins its source, hashes and acceptance limits.

TD separately saved the configured live working project as
`ROTO-CONTROL.mix-analysis.2.toe` in the original project's current directory,
with adjacent identity receipt. Its SHA-256 is
`9d0efeda58df2dc53191177ef6a0a2b358622363482420f393f1596858e810c2`.
The old local canonical `ROTO-CONTROL.toe`, its receipt and this worktree's
checked-in demo remain untouched. The original dirty checkout's runtime source
was neither copied into TD nor changed. Original values/mappings, the old
controller's 246 DAT fingerprints and all eight demo-network children, including
the user's audio nodes, match the pre-publication snapshot. TD stays open and
disconnected; no full main-project restart is claimed.

Recovery, scripts, export/reload results and the pre-save working file are in
system temporary `roto-mix-publish-vyql43ej`. The two new committed files for
distribution are the generic tox and its receipt; probes remain temporary.
Reuse the final 511 source tests and targeted native/physical evidence because
publication changed no runtime behavior.
