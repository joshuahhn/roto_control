# ROTO-CONTROL Python handoff

## Current State

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

## Known Issues

Single-target mode is physically accepted. Collection supports up to 8 knobs/8 PLUGIN buttons in software; physical acceptance is in progress. No bank/page editor, MIX or transport controls. macOS was tested; other platforms are unverified. Numeric display is a temporary firmware overlay. No full-day reliability or USB hot-plug acceptance is claimed. Disconnect before source reload; extension reinit deliberately resets connection state.

TD 2025.33230 native MIDI receive defects are avoided through the external Python process, not fixed. No native MIDI operators are added to this project's user network. TD's system MIDI operators are unchanged.

## Resume Steps

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

`pixelSortV3` and `fractal_pop` are now the saved 13-target collection; the user had cleared all prior demo bindings before this run. `real_component_setup.py` is the reproducible installer. Eight numeric targets, three Toggle targets and two Pulse targets span both Inspector COMP pages. Slots 5–7 buttons stay Unassigned; no functional operators were added inside the user's COMPs.

API now supports writable same-style Par BIND chains ending at CONSTANT masters. Expressions/exports/readonly roots, missing/cyclic/non-Par masters and shared aliases are rejected, and all numeric clamp limits are validated. Target aliases retain their BIND mode/expression. 95 automated tests pass. Live `verify_real_components.py` verified real software writes, public/master edits, all 13 synthetic mappings and input, Int rounding, camera bound Reset exactly once and both Pulse watcher acknowledgements, node marks, pages, Disconnect catalog, deletion/restore and empty Clear All. Original target values, camera transform/pivot and the temporary Reset observer were restored. Physical LEARN acceptance remains pending.

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

116 unit tests pass. verify_free_learn.py exercised an actual unregistered new COMP Par change through native onValuesChanged, then simulated matching hardware slot acknowledgement, numeric input, preserved unrelated mapping, observer shutdown, API-write exclusion and extension reload with dynamic index retained. An initial same-frame watcher setup/change missed the callback; the actual verification now initializes observation for one frame before changing the parameter, matching hardware LEARN followed by slider interaction. Temporary fixture removed. Physical direct learn is pending user test on sortError.

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

External layout_protocol_probe.py and LAYOUT_PROBE.md prepare the A/B/A hardware gate. Probe has its own MIDI lifetime, distinct synthetic identities, ordered RX/TX log, requested versus control-confirmed state, lock/LEARN/touch guards and no UNMAP/user-target writes. It has not been started and physical recall remains unverified. Production TD must be disconnected before probe port ownership; stop/close ports then reconnect production to restore.

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

154 automated tests pass. Disconnected native fixture verified same-name Track isolation, Inspector context, clear-confirmation expiry, synthetic Track selection/mapping/input, native Track dropdown and New Track pulse, and actual tox save/reload with identities/assignments preserved. Fresh builder passed. Generic export reload verified one empty Layout/Track/Plugin, no assignments/deletion records, no external DAT file dependencies and no MIDI process. Evidence: multitrack_native_verification.json; repeatable native stages: verify_multitrack.py. Native synthetic input is not physical acceptance. Fixtures removed; network check covers 4 networks, 17 groups, 63 operators, with containment and no overlap/backward wires.

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

162 tests pass, including eight pages with 8 knobs plus 8 buttons each (128 definitions), A/B/A, reconnect, Clear isolation and empty-page input gating. Native fixture passed actual parameter writes, two-page recall and tox save/reload retaining off-page targets. Generic .28.tox reload is empty/disconnected with no external DAT references; network layout unchanged and clean. Evidence: control_pages_native_verification.json; native harness: verify_control_pages.py. Saved roto_control_python.44.toe and promoted canonical project/export. Main connection requested for physical retest. Current preserved T Plugin library contains Mix at index 129; records previously deleted by the old implementation cannot be inferred from unknown hashes and must be re-learned once. Physical control-page acceptance is pending; previous Track acceptance remains separately scoped. No commit/push.


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

192 unit tests pass. Native fixture passes current/selected disagreement, zero/mixed/multiple selection, unchanged values/Pulse, idle no-op, same-batch/backlog fences, fresh recall, LOCK/LEARN/touch, stale-session cancellation, offline Follow, repeated upgrade and managed tox reload. Actual stopped-timeline project.save followed by project.load retains renamed Focus links and saved routing with Follow=True, valid restored target, no pending activation and no MIDI process. Native executeDAT introspection exposed projectpresave (omitted from the tool catalog); enabling it is required for onProjectPreSave. Unresolved Focus UI references after rename are resynchronized rather than interpreted as unlink. Fresh builder passes; export reload clears Follow/links/targets/file dependencies, including export before a clone's first Tick. Evidence: comp_follow_native_verification.json; reproducible stages: verify_comp_follow.py.

Main comparison against live_select_before.json preserves all Layout/Track/Plugin/target IDs, target configuration, Mix/Sortcrit off-page library, Lowthresh Track and original custom parameter values. Both pixelSortV3 Tracks remain unlinked; Follow is off. One new textDAT and Focus annotation add no signal wires. Four networks/18 groups/64 operators pass containment/no overlap/backward-wire checks; controller errors are empty. Source docs embedded. Final artifacts: roto_control_python.55.toe and empty generic exports/roto_python.32.tox; canonical copies match. Main external reconnect is checked separately below. Physical Follow A/B/A, current feedback and guarded switching remain pending; earlier manual Track acceptance is not reused for this feature. Controller-reparent stress and ordinary mouse-click ergonomics retain further acceptance gates. Hardware-to-TD selection and Layout/Plugin name synchronization are deferred. No commit/push.

Main external reconnect after the final save/export passed: T / TRACK / PLUGIN, Knob 1 Lowthresh mapped/valid, Connected/Plugin=True, no Lasterror or operator errors. Main remains connected for testing; saved startup remains disconnected. This is recall verification, not new physical Follow acceptance.

Physical single-COMP Follow test: user confirmed "working" after pixelSortV3 selection activated T / T / CUSTOM and Knob 1 recalled Sortcrit. Live inspection showed mapped/valid Sortcrit=4 (Red), no errors. This accepts the reported selection/knob workflow; LCD was not separately specified. Two-COMP A/B/A, Follow LOCK/unlock and LEARN/touch acceptance remain pending. Test link pixelSortV3 -> Track T and Follow=True remain live; naming is unchanged and the link has not been promoted into the saved canonical project. Evidence: comp_follow_hardware_verification.json.

## Independent Device context / registry v3 (2026-10-07)

User approved proceeding after Ableton/Bitwig/Logic comparison. Track now explicitly groups 1..127 Devices (Plugins); each owns separate identities, current targets and off-page library. Hardware SEL has eight-item Device metadata banks and independent Plugin selection. COMP Follow resolves (Layout, Track, Plugin), with Plugin-owned Focus links. v1/v2 migration preserves existing groups, IDs, wire hashes, target specifications/removal/relearn state and libraries; existing T / TRACK mapping variants were not merged. v2 Track Focus moves to its sole Plugin. Linked Device names follow actual COMP names; Layout names remain independent. Full COMP name stays in the selector, hardware uses at most 12 printable ASCII bytes. RenamePlugin opts into manual naming; SetTrackComp remains an active-Device compatibility wrapper. Added GetPlugins/CreatePlugin/SelectPlugin/RenamePlugin/RemovePlugin/SetPluginComp. Layout custom page has 16 fields in three sections; no new Binding modes or permanent confirmation buttons.

Same-Track Device switches use the existing fenced arbiter, backlog/partial-line epochs, fresh recall and connection-generation cancellation. LOCK blocks automatic TD Follow and hardware Track routing, but explicit hardware Device selection can replace the locked Device within its routing Track after LEARN/touch/backlog guards. Selected Track divergence persists and unlock follows current selection. Activation/rollback/domain/transport failure policies remain. Hardware-to-TD UI selection/reveal, auto-macros and Device bypass/enable remain deferred.

Native rename-before-tox-save found stale saved target paths despite a valid Focus link. Fixed rebasing destinations inside the linked live COMP across active and inactive mapping variants, retaining target IDs/hashes; also updates assignment/library storage. Source upgrade now force-captures current configuration before source replacement. Generic export clears arbitrary root storage backups before rebuilding documented empty state, so older verification snapshots cannot carry user mappings into the reusable tox.

209 unit tests pass, including same-Track A/B/A, ninth-Device banking, invalid indices/capacity, Clear/library isolation, mixed-source arbitration, LOCK exceptions, LEARN/touch/backlog, actual Tick partial-line epochs, reconnect cancellation, rollback failure, duplicate links, rename/rebase and popup expiry on all three IDs. Existing schema tests now assert Device-owned Focus with the same behavior checks. Native TD 2025.33230 fixture passes two-COMP same-Track Follow without value/Pulse writes, actual parameter/Pulse dispatch, fenced old input, fresh recall, locked Device selection, ninth-Device list/select, repeated upgrade, managed tox reload and actual stopped-timeline project.save/project.load with valid renamed target/link/name. TD restarts its global clock on load; reopened fixture checks were explicitly run paused again. Bridge recovered after reload; temporary Textport diagnostics were used to inspect the clock. Evidence: device_context_native_verification.json; harness: verify_device_context.py.

Main baseline deep comparison preserves IDs, targets, libraries, mapping variants and native values. Fresh external builder, native Active Device custom-parameter callback after watcher initialization, Python registration reconstruction/parameter return and generic export reload pass. Generic export is empty/disconnected, Follow off, no links, user backup mappings, DAT file dependencies or child process; embedded docs match source. Four networks / 18 groups / 64 operators remain clean with no new production topology. Upgrade/export/reconnect evidence: device_context_upgrade_verification.json; baseline: device_context_before.json.

Saved through TD as roto_control_python.57.toe (explicit .56 destination also produced TD's incremented .57); canonical project bytes match .57. Generic exports/roto_python.33.tox is verified and canonical tox bytes match. Authoritative source docs embedded with geometry retained. Main external reconnect passed on original T / TRACK / PLUGIN context: Lowthresh mapped/valid, no re-LEARN requirement, Connected/Plugin true and no errors. Main is connected for testing; saved startup is disconnected. Existing linked T Device now displays pixelSortV3; unlinked TRACK Device keeps its manual PLUGIN name. Follow preference retained. Temporary fixtures and controller verification snapshots removed. Physical multi-Device SEL/LOCK/motor/LCD acceptance remains pending; prior manual Track acceptance is not reused. No commit/push.

## Delayed Free LEARN acknowledgements / Menu Button (2026-10-07)

User reported Knob 2 Lowthresh and Button 1 Mask Image (pixelSortV3.Masksource) missing from T / T / pixelSortV3. Targeted physical trace confirmed Lowthresh offered first, Masksource offered later with the same unreserved index, and mapping reports arriving together only on LEARN exit. Masksource's Button ACK arrived first but was rejected because no selection CC had reached TD and the offer defaulted to knob; Lowthresh's older ACK then had no pending target. Existing Knob 1 Sortcrit, Knob 3 Highthresh and newly learned Knob 4 Mix remained valid.

FreeLearner now retains offers independently by index/hash for 30 seconds, reserves uncommitted indices, reuses a pending parameter's ID/index and accepts out-of-order ACKs. The 128-offer limit rejects new offers without discarding older ones. Existing pending=None invalidation on Layout/Device/page/fence/session resets clears the entire cache. Menu kind is resolved from its ACK even without selection CC; knob value or button Cycle adapters retain the offered hash, persisted with unchanged options in the Device registry. Changed Menu options still reject commit; non-Menu type mismatch remains guarded.

216 unit tests pass. Native actual Parameter Execute edits reproduce newest Mask/Button ACK before older Lowthresh/Knob ACK after LEARN off; both commit without value writes, dispatch succeeds, and extension reload preserves hashes for fresh recall. Evidence: lowthresh_button_learn_trace.json and learn_overlap_native_verification.json; harness: verify_learn_overlap.py. Main before/after comparison preserves all current IDs/hashes, libraries, contexts and pixelSortV3 values, including the user's new Highthresh/Mix registrations. Temporary method probes and fixtures removed. Four networks/18 groups/64 operators retain containment, no overlap/backward wires and no errors. Updated controls Markdown embedded. Generic .34.tox reload is empty/disconnected, Follow off, no Focus link or MIDI process, with updated code/docs. Saved through TD as roto_control_python.59.toe; canonical project/export promoted. Failed Lowthresh/Mask mappings were never saved by the old code and require new physical LEARN; post-fix physical acceptance is pending. No commit/push.

Post-fix physical acceptance passed: user re-learned Knob 2 Lowthresh and Button 1 Mask Image and confirmed both respond normally. Live checks show both mapped/valid, Masksource mode Cycle; existing Knob 1 Sortcrit, Knob 3 Highthresh and Knob 4 Mix remain mapped. Evidence: learn_overlap_hardware_verification.json. Saved accepted mappings through TD as roto_control_python.61.toe and promoted its bytes to canonical project; generic .34.tox remains unchanged and empty. Saved startup is disconnected; live controller reconnects for continued use.

## Cycle LED / LCD feedback (2026-10-07)

User then reported Button 1 LED always off/immediately cleared and its Menu LCD staying on Source. A deterministic two-choice Menu test reproduced TOGGLE feedback sending zero after advancing to the second choice; PUSH also retained the press latch when software selected the first choice. Cycle shared Pulse's _pulse_state for LED output, despite having a persistent Menu value. Control._feedback now uses selected Menu state for Cycle LED: first option off, other options on. RX press/release state remains separate, and Pulse's established idle/press feedback is retained. No parameter name, COMP or slot is hardcoded; existing IDs/hashes and assignments stay unchanged and require no re-LEARN.

218 unit tests pass, including TOGGLE/PUSH two-choice LED state, software writes, PUSH release, three-choice wrap/nonfirst state and selected-option LCD packets. Live trace shows Button 1 CC feedback and matching option text; the user confirmed LED and LCD both switch normally after this change. No additional display command or label change was needed; TD labels remain Source (Input 1) / Control (Input 2). Evidence: cycle_feedback_before.json and cycle_feedback_hardware_verification.json. Temporary send/receive probes removed. Main five controls retained; network geometry remains four networks/18 groups/64 operators with no overlap/backward wires or errors. Updated controls Markdown embedded. Saved through TD as roto_control_python.63.toe and exported empty generic exports/roto_python.35.tox; canonical copies promoted. Saved startup stays disconnected, live MIDI reconnects for use. No commit/push.

## Tagged COMP discovery / separate Layout and Device pages (2026-10-07)

User chose separate Layout and Device contexts: Layout T stays a mapping set, Track T groups Devices, pixelSortV3 and fractal_pop each own their mappings. Explicit roto_device OP tags register a Device in Active Layout / Active Track during an idle scan, approximately once per second. Existing links anywhere in Active Layout are reused; removing a tag retains saved mappings. Registration respects LEARN/touch/LOCK/routing/transport guards, Track capacity and transactional rollback. Follow handles adding a tag to an already selected COMP, including an existing linked Device, while retaining startup selection baselines. No per-COMP Layout creation or Layout/Device name synchronization.

FreeLearner rejects edits outside the active linked Device's COMP subtree; nested linked Devices own their more specific scope. Discovery and delayed ACK commit apply the same check. Unlinked/manual and Python registration compatibility remain. The outer UI now separates Layout (10 fields) and Device (6 fields), retaining parameter names and APIs. Labels identify Active Layout (mapping set), Active Track group (FUNC), and Active Device (SEL). No new Binding mode, confirmation button or production operator.

228 unit tests pass. Native TD 2025.33230 fixture verifies actual OP tags, Parameter Execute LEARN, foreign-COMP rejection, isolated dispatch/libraries, rename/reload/hash recall and idempotent UI migration (tag_device_native_verification.json; verify_tag_devices.py). User physically confirmed fractal_pop Knob 1 Power responds and returning to pixelSortV3 restores its original mappings; Layout stays T (tag_device_hardware_verification.json). This accepts tagged-COMP Follow/LEARN/recall, not physical SEL/LOCK/motor/LCD switching.

Main source reload preserves all mapping configuration, identities/libraries and target values, including the newly learned fractal_pop Power. PixelSort's five mappings recall on external reconnect, with no runtime errors. Temporary probes/fixtures removed; four networks/18 groups/64 operators retain clean geometry. Updated authoritative docs embedded. Final live-TD save: roto_control_python.67.toe; generic exports/roto_python.37.tox reload is empty/disconnected, Follow off, no Focus link or MIDI process, and embeds current source/docs. Canonical copies promoted; saved startup is disconnected, live MIDI reconnects for use. Intermediate .65/.36 snapshots precede the final physical-acceptance documentation. No commit/push.

## PR #1 Device metadata index follow-up (2026-10-07)

Followed up the PR's Ableton-comparison comment (issuecomment-6027764498). Regression tests reproduce deleting A from [A, B, C] while B is active, or deleting active A after selecting B as successor: the list becomes [B, C] but host.plugin_index remains 1. remove_plugin now recomputes the active Device index from the final list even while disconnected. Host.set_display_names sends Device details only when the Device name changes, so Track-only rename does not resend Device metadata. Upstream Ableton/Bitwig sources remain unchanged; the reported lack of an explicit Ableton Device-deletion listener remains an unverified observation.

230 unit tests pass, including metadata index after both deletion paths, subsequent Device rename and Track-only rename without identity/library changes. Native TD 2025.33230 isolated clone passes the same cases without physical MIDI I/O (verify_device_metadata.py; device_metadata_native_verification.json). Fixture removed, main project/mappings untouched. This follow-up changes local source only: live main and canonical .67.toe/.37.tox still contain the prior runtime and have not been upgraded/exported for this fix. No physical acceptance, commit, push or GitHub reply posted.

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

User physically confirmed K2 value updates and LEARN on/off alerts both work. Native checks additionally pass Value Apply/event refresh, inactive fractal_pop Power updates through a parameter watcher, route-preserving browsing, single-main-window behavior, session/revision guards, and generic tox reload with no controller link or saved destinations. UI export/reload retains the production connected session/catalog. 230 runtime + 21 Inspector model tests pass, with no operator/subscriber errors. Read-only sync probe p95 is 0.395 ms over 100 calls; unchanged snapshots write no text and 1,000 requests retain one scheduled run. This does not establish total rendering performance or long-duration memory stability. Evidence and current limitations: prototypes/inspector/LIVE_REPORT.md and live_*.json.

TD was restarted after the user's request using inspector_restart_checkpoint.1.toe. Initial live-TD checkpoint inspector_real_data.1.toe reloads the real adapter, preserves IDs/context and user values within TD serialization precision (maximum observed float delta 1.72e-7), and starts MIDI disconnected. Live controller was reconnected and only the Fold Inspector is open. Generic inspector_model.tox / inspector_below.tox / inspector_popup.tox embed code and start with no configured controller or user destinations. Canonical roto_control_python.75.toe and exports/roto_python.40.tox were not replaced. No commit/push.

User renamed the displayed BELOW style to FOLD. UI label, presentation menu and window title use Fold; internal component/style identifiers remain below. The latest inspector_real_data.toe save includes this label and an embedded snapshot of the prototype README.

## Compact Inspector Ping / Clear (2026-10-07)

Both Fold and Popup editors now use 24 x 24 icon actions: Ping/Clear top right, Cancel/Apply on the right of the status/Value edits live target row, with hover descriptions. The user's spacing refinement uses 12px side insets, 6px row/control gaps and a 178px editor height without the spare footer space. Ping uses existing Offerparameter and requires hardware LEARN/PLUGIN plus the selected active registration; sending is explicitly awaiting ACK, with no Value/Pulse action. Clear uses RemoveControl, retaining the target Value, after a second inline click within eight seconds. Context/session/revision checks and LEARN/touch guards protect removal. Mapping metadata stays read-only; inactive browsing cannot mutate controls.

230 runtime + 33 Inspector model/editor tests pass. A disconnected native clone verifies forgotten-map metadata output, LEARN guard, Pulse isolation, Clear confirmation and single-registration removal without production catalog/registry/session changes. Geometry and operator errors pass. Physical Ping/re-LEARN acceptance is pending. Source builders and generic UI exports include the new controls; latest project checkpoint is inspector_editor_actions.2.toe, preserving the user's Popup preference with one main Inspector and no open editors. See prototypes/inspector/editor_actions_verification.json. No production runtime edits, commit or push.
