# ROTO-CONTROL Python handoff

## Current requirements and entry point

Use [AGENTS.md](../../AGENTS.md#change-scoped-validation) for validation requirements and [OPEN_PROJECT.md](OPEN_PROJECT.md) for the current saved project. Source checkout and saved runtime are distinct: see [CONTEXT.md](CONTEXT.md#checkout-and-artifact-scope). Local main is behind remote main; issue #15 was merged through PR #17, not left pending upstream.

Reuse dated acceptance when the relevant behavior and environment are unaffected. The latest applicable result supersedes an earlier pending statement for that same case only. Historical counts, paths, connection states and Resume Steps below describe their date; they are not instructions to reopen old artifacts or repeat all checks. Relocated evidence is indexed in [diagnostics](diagnostics/README.md), including the old/new path manifest.

## Unresolved limitations, not automatic tasks

- This checkout's recorded physical coverage does not establish ninth-Device banking, guarded/locked TD Follow or control-page re-LEARN/recall acceptance. Revisit only when affected by the requested change or explicitly requested.
- Non-macOS behavior, full-day reliability and USB hot-plug acceptance are not established by these records. Native MIDI receive investigation remains separate from the production external MIDI backend.
- Reconcile local source and the saved owned Inspector candidate before source-driven live upgrades. Remote main already contains later implementation; synchronizing the dirty checkout is separate from this documentation change.

## Accepted evidence to reuse within its scope

- Later 2026-10-07 entries accept delayed Free LEARN ACKs, Cycle LED/LCD, tagged-COMP Follow/recall, unlocked Device metadata/SEL, LOCK selection, and the tested mapped-control/motor/isolation cases. Earlier pending statements for those cases are historical.
- The 2026-10-11 entries record current-project reopen/controller checks and Python portability/export acceptance. Their source and artifact scopes differ; they do not establish parity of every checkout or unrestricted hardware coverage.

## Historical record — first milestone (2026-10-03)

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

## Historical known issues (2026-10-04)

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

### Portable Python interpreter / Connection buttons — 2026-10-11

Connect/Disconnect Pulse callbacks both dispatch correctly. Connect remained at
Opening MIDI ports because the timeline was paused and lifecycle Tick is frame-driven;
Disconnect terminated the child even while paused. User confirmed operation after
Play. Polling behavior is retained; portability docs now explain the timeline requirement.

Interpreter resolution accepts a short PATH command, project-relative venv, home-relative
or absolute interpreter and preserves venv entrypoint symlinks. Seven Connect regressions
include red-before/green-after PATH and home-relative cases. Applied only this scoped
runtime change to both original source and issue15 candidate; unrelated candidate fixes
were not installed into the live project.

Live Python is ../../.venv/bin/python. Generic export defaults to python3 instead of
serializing this machine's absolute interpreter. The PATH Python on this machine lacks
mido/python-rtmidi; generic users must install dependencies or configure their own venv.
Current project's existing venv reconnects successfully with Connected/Plugin/Mapped
true, Rejected0 and no TD errors. Mapping definitions, identities, Snapshots, parameter
values and geometry match baseline; restoration only hydrates identity/Menu metadata
from unchanged saved targets, while registry revision and transport readouts are transient.

Original237/candidate449 runtime tests and Inspector248 pass. Generic tox live load
passes empty/disconnected/Follow-off/no-Snapshots/no-DAT-file-dependencies/local owned
Inspector checks. Saved through live TD to original projects/current/ROTO-CONTROL.toe
(disconnected startup), updated identity receipt and canonical exports/roto_python.tox
from new roto_python.portable.20261011.tox. Live is reconnected with timeline playing.
Recovery toe/tox/source are retained in projects/archive/python-portability-recovery;
evidence and external harness: diagnostics/runtime/results/python_portability and
diagnostics/runtime/verify_python_portability.py in the original checkout.
Candidate canonical artifacts remain unchanged. No commit/push or inherited source changes.

## Artifact sync — 2026-10-12

Current `/roto_clean_demo/roto_python` runtime, watcher callbacks, embedded MIDI helper
and 16 principal Inspector source DATs matched merged main `2de08c9` before changes.
No runtime reinstall was needed. Updated five embedded Markdown snapshots from that
source (README, actions, inspector, lifecycle, portability), preserving geometry.
Live TD 2025.33230 saved `projects/current/ROTO-CONTROL.3.toe`; canonical
`ROTO-CONTROL.toe` matches its bytes. Refreshed `projects/current/project.json`.

Exported `exports/roto_python.synced.20261012.tox` through live TD and promoted its
bytes to `exports/roto_python.tox`. Native reload passed runtime/Inspector parity,
local Inspector ownership, empty mappings/Snapshots, disconnected startup, Follow off,
Python=python3 and no DAT file dependencies. Original mapping registry, Snapshots,
parameter values and geometry match the pre-operation baseline; zero scoped errors.
Live project remains disconnected, as found. No new hardware acceptance is claimed.

Recovery copies of prior project/export/receipt and configured controller are retained
in `projects/archive/sync-20261012-recovery`. One-off harness/results are in the system
temporary directory `/private/tmp/roto-artifact-sync-20261012`. Original dirty local
main/source checkout was not synchronized; other project components were not upgraded.
No commit/push or changes to issue #6.

## LEARN metadata source refactor — 2026-10-16

User approved the first capability-plan step: isolate LEARN metadata without adding feedback APIs or changing queue/routing policy. Local source now uses immutable `protocol.LearnParameter` metadata and the pure `learn_parameter_message` encoder. Legacy Host, collection controls and Free LEARN share the encoder; `Controls.specs` passes Menu labels explicitly. Free LEARN retains metadata for pending offers instead of creating a temporary Control and setting session flags. Formatter introspection is removed. Existing index/hash, Menu signatures, pending-offer expiry, mapping ACK handling and target writes retain their prior paths.

The checkout remains dirty local `1cb09d9`; pre-existing edits were preserved, including the interpreter changes in RotoPythonExt. Its two replacement-Control paths now also pass Menu labels. Three regressions cover formatter-independent Menu packets, the 16-label boundary at 2/16/17/24 choices, and Free LEARN versus registered metadata with no target value/Pulse writes. `python3 -m unittest discover -q` from this checkout's `src/touchdesigner` passes 240 tests.

The same scoped refactor was adapted to a system-temporary source extraction of saved receipt commit `2de08c9`, retaining its later transaction/ownership fixes; its same discovery command passes 472 tests. Each baseline's before/after corpus of 163 complete LEARN messages is byte-identical, covering all physical slots, Menu sizes 2..24, numeric and button offers, Free LEARN and the legacy Host. A Python inline-module import probe also passes; this is not native TD acceptance. Regression tests are retained above; the one-off packet capture and baseline patches are in `/var/folders/5q/krg7wb4d4lsgpmlmgqvywj_w0000gn/T/roto-learn-metadata-opmbqmh1` (`capture_packets.py`, `local-refactor.patch`, `saved-refactor.patch` and before/after JSON outputs). The saved patch is based on `2de08c9`, not the dirty root checkout.

Source-only delivery: current `.toe/.tox` and their receipt remain unchanged, with saved runtime still at `2de08c9`. No native TD reload, new physical acceptance, save/export, commit or push. A future live integration must use the saved-baseline patch or an equivalent scoped application to the chosen current source, rather than install this older checkout wholesale.

## Main-screen context first — 2026-10-16

User selected current COMP/Device context as the first feedback use case, initially with a short indication on switching. After the concept preview, the user explicitly prioritized the main screen; Screen 8 is a fallback only if the main screen cannot meet the actual need. Reuse the native Menu Window Track/Device names before adding an overlay. No timed popup, name-spoofing mechanism or Screen 8 context output was implemented.

Checked official upstream `2d43a72c6699983080f8765292498502ff08be57`: local SysEx v1.6 and Serial v1.3 PDFs and the examined Ableton/Bitwig/Logic integration files match upstream bytes. The manual's PLUGIN section identifies the Menu Window Track/Device display. SysEx `0A 16` updates the current Track name; `0B 05/06/08` supply Plugin details/end/selection. Names carry 12 ASCII characters plus NULL. No independent main-screen popup/timeout command is documented; `0A 18` addresses knob/switch controls 0..7. Serial setup/Plugin name writes are configuration operations and were not used as a live display workaround.

Existing metadata/context tests passed on the dirty local `1cb09d9` source, 3+19 tests, and on the system-temporary saved-receipt `2de08c9` source with the prior scoped LEARN refactor, 3+21 tests. A further one-off host-output probe passed seven scenarios on each baseline: direct A/B/A Device selection, LEARN/touch/backlog deferral, locked explicit Device selection and unlock to the selected Track. It checks advertised Device name/index/hash against the routing Device, unchanged target values/identities for direct switching, no advertised Device activation while guarded, retained LOCK/selected-Track distinction, no forced page selection and no context `SHOW CONTROL VALUE` output. This is source-output evidence, not a firmware display emulator or physical screen acceptance. Probe source is in the system temporary directory `/var/folders/5q/krg7wb4d4lsgpmlmgqvywj_w0000gn/T/roto-main-screen-5yib9jw7/probe_context.py`.

No runtime gap requiring an additional context message was found in these cases. Documented the existing behavior and main-screen-first policy in `docs/functions/layouts.md`. Reuse the historical Device metadata/LOCK acceptance above for its original scope; it does not establish a new transient popup or exact locked Track-field rendering. The configured local TD MCP endpoint `http://127.0.0.1:13316/mcp` returned `Connection refused`, so the active project and current controller screen could not be inspected. No MCP configuration/install changes, live TD/controller I/O, runtime source changes, artifact embedding/save/export, commit or push in this step.

## Main-screen physical check — 2026-10-16

After the user opened TD and replied ready, the configured MCP connected successfully without configuration changes. Verified `ROTO-CONTROL.3.toe` in `projects/current`, controller `/roto_clean_demo/roto_python`, TD 2025.33230, and eight principal runtime DATs byte-identical to saved receipt source `2de08c9`. This live session contains the user's existing COMP-owned `demo_A` and `demo_B` Layouts; it is not the older pixelSort/fractal context. Captured its actual registry, controller parameters, linked COMP values/modes, Snapshots and source hashes before connection. The prior LEARN refactor was not installed or accepted by this check.

Connected the existing external MIDI backend to `Roto-Control`. Firmware query returned 3.3.0, commit `eaa37b0`; SysEx API query returned 1.6. A temporary receive wrapper forwarded normal messages and removed itself after both responses; the original receive method is restored. No serial access, firmware update or MCP installation. Official 3.3.0 release notes were checked for relevant UI changes; the downloaded PDF and extraction remain in the temporary evidence directory.

Physical observations confirmed by the user:

- Initial normal PLUGIN view showed `demo_A` with a blank/underscore lower line, although the host Track name was `EFFECT`. A direct `0A 16` current-Track-name message did not change that line.
- Sent the existing Track/index again using official Ableton-style `0C 04`. The user then found `EFFECT` in FUNC's Track list and selected its first button; normal main view showed `demo_A / EFFECT`. That combined sequence does not isolate the packet alone as a fix. Initial Track-field rendering is an unresolved refresh issue, not evidence that the main screen is unavailable.
- TD `SelectLayout` to existing `demo_B` changed the main screen to `demo_B / EFFECT`, with the eight control screens normal. Returning to existing `demo_A` showed `demo_A / EFFECT`.
- The user enabled hardware LOCK. TD observed it; an attempted TD Layout switch to demo_B raised `Unlock hardware before switching Layout`, changed no registry/context and emitted no MIDI. The user confirmed the main screen retained `demo_A / EFFECT`, then physically unlocked.

This accepts native main-screen Device context and the tested A/B/A / TD-origin LOCK case. It does not accept a timed popup, divergent selected/routing Track rendering, same-Track hardware SEL switching, new LEARN behavior or unrelated motor/control behavior. Keep Screen 8 deferred. No runtime change was needed for the tested Device context; initial Track-line refresh needs a separately scoped diagnosis rather than a speculative timer/queue/transport change.

Ordinary connection recall reported existing stale/Menu mapping issues and reconciled pending unmaps, temporarily changing cached active definitions. No parameter value, Pulse action or LEARN was deliberately invoked. Restored the entire original TD registry and active four-control configuration while disconnected, preserving monotonic registry revision. Verified original IDs/targets/state except revision, both linked COMPs' values and modes, all controller parameters, Snapshots, Follow=True, LOCK=False, original demo_A context and disconnected/no-process session. The eight captured runtime DAT hashes match the initial live baseline; zero scoped TD errors. Controller internal learned storage was not read back for a full comparison, and ordinary reconciliation traffic is not claimed as no hardware unmaps.

Recovery/probes/results remain only in `/var/folders/5q/krg7wb4d4lsgpmlmgqvywj_w0000gn/T/roto-main-screen-5yib9jw7`, including `live-baseline.json`, `live-source`, `hardware-versions.json`, `physical-observations.json`, `lock-guard.json`, `live-pre-restoration.json` and `live-restoration.json`. No runtime source edits, builder/reload, save/export, embedded-doc refresh, commit or push. TD remains open; canonical toe/tox and receipt are unchanged. Only these authoritative Markdown records were updated.

## Different Track-group display check — 2026-10-16

User requested a different group to see whether the main screen updates. Reconfirmed the same active project/controller, captured a fresh baseline at registry revision 183, and connected the existing backend. Within the existing demo_A Layout, created one temporary second Track named `GROUP TEST` and renamed its automatically created empty Device `TEST DEVICE`. No targets or mappings were added. TD `SelectTrack` selected that Track at index 1; the user confirmed the main screen immediately showed `TEST DEVICE / GROUP TEST`, without FUNC. Selecting the original index-0 Track immediately restored `demo_A / EFFECT`, also confirmed without FUNC. This establishes normal distinct Track-group updates in both directions on firmware 3.3.0 / API 1.6; it does not resolve or reclassify the earlier initial-connection Track-line issue.

Removed the temporary Track via the public API, then restored the complete fresh baseline while disconnected. Registry/configuration matches except monotonic revision, original four controls/IDs are restored, controller parameters, linked COMP values/modes, Snapshots, Follow, LOCK and original context match, and eight runtime DAT hashes are unchanged. No target value or Pulse/LEARN action was invoked; no new source code or artifact save/export. TD remains open with the original disconnected session. The normal recall/reconciliation limitations from the previous physical check still apply.

Fresh baseline, fixture IDs, scripts and restoration result are retained only beside the previous temporary evidence as `group-baseline.json`, `group-fixture.json`, `group-live-source`, `group-pre-restoration.json`, `group-restoration.json` and `group-physical-observations.json`. Authoritative Layout documentation was updated; Screen 8 remains unused.

## Parameter-page caption prototype, three physical round trips — 2026-10-17

The user chose the TD custom-parameter page belonging to the currently mapped hardware controls, rather than TD's open parameter tab. Reconfirmed `ROTO-CONTROL.3.toe` and the same controller/backend/firmware, capturing a fresh disconnected baseline at registry revision 197. The acknowledged controls after normal recall were Knobs 1–3, targeting demo_A Amount, Steps and Mode, all on the TD `Demo` page. A manual probe read those actual bindings and sent `Demo` with current-Track-name command `0A 16`, without changing the software Track name. The user confirmed main screen `demo_A / Demo`, then corrected the FUNC-list observation to `EFFECT`. Thus the tested main-screen caption and Track-list name can differ; the correction supersedes the preceding report of `Demo` in that list.

At the user's request for repeated testing, created an empty temporary TD custom page `Controls` on demo_A. The dedicated custom-parameter tool reported success without creating an empty page; a documented `appendCustomPage` call created it instead. No parameter moved during that failed setup attempt. Each test step moved only the same three acknowledged parameters between `Controls` and `Demo`, derived their common page name, and manually sent that caption. Three complete round trips, six individually confirmed screen states, passed: `demo_A / Controls` then `demo_A / Demo` each time, with normal eight control screens and no FUNC operation. Each step checked matching mapped slot/target identities, unchanged linked-COMP values/modes and software Track `EFFECT`. This changes TD parameter-page metadata, not hardware control-page assignments. It does not accept automatic page feedback, hardware arrow-page recall, mixed/callback targets, mode/selector recovery, a timed popup or the earlier initial Track-line refresh issue. No new LEARN or business parameter/Pulse writes were invoked; ordinary connection reconciliation has the same limitations recorded above.

Restored all original parameter page memberships and order, verified the temporary page was empty before destroying it, and sent the real Track caption `EFFECT`; the outbound queue drained before Disconnect. Restored the complete fresh software baseline except monotonic registry revision 203. Original four control definitions/IDs, controller parameters, linked-COMP values/modes, Snapshots, Follow=True, LOCK=False and demo_A context match; eight principal runtime DAT hashes are unchanged. TD remains open, disconnected with no MIDI child. Native scoped errors are zero. Caption output draining is transport evidence, not an additional physical observation after restoration.

Temporary evidence remains in `/var/folders/5q/krg7wb4d4lsgpmlmgqvywj_w0000gn/T/roto-main-screen-5yib9jw7`: `page-baseline.json`, `page-live-source`, `page-label-probe.json`, `page-cycle-state.json`, the page-step/restoration scripts, `page-presentation-restoration.json`, `page-pre-restoration.json` and `page-restoration.json`. Runtime remains saved source `2de08c9`; no production page-feedback implementation, runtime source edit/reload, save/export, embedded-doc refresh, commit or push. Only the authoritative Layout documentation and this handoff were changed for this result; Screen 8 remains unused.

## Automatic parameter-page hint — 2026-10-17

After the user requested the next step, implemented the agreed brief main-screen hint. `Controls.mapped_page` reads the public TD parameters of acknowledged slots and returns a common COMP/page only when unambiguous. `RotoPythonExt` sends that page name through existing `0A 16`, then restores the real Track name after a two-second deadline on the next safe Tick. Different pages/COMPs, callback/action targets, invalid targets and empty mappings use the Track name. Existing LEARN/touch/LOCK/restore/context/backlog guards defer output; existing queue fences remove old hints. Native Device/Track announcements and control-page changes invalidate the hint cache. No new timer, UI parameter, DAT, queue adapter or Screen 8 output; no changes to target writes, names, FUNC metadata or wire identities.

Preserved the dirty `1cb09d9` checkout and separately adapted only this delta to a fresh system-temporary `2de08c9` extraction. Nine regressions cover deadline/restoration and duplicate suppression, native page metadata changes, matching versus rejected ACKs and partial readiness, mixed pages/COMPs, callback/invalid targets, empty/same-name page recall, guards, session/selection replay and queued-hint removal by the existing fence. `python3 -m unittest discover -q` passes 249 tests on the final local runtime source and 478 on the saved-baseline candidate. The reusable [saved-baseline patch](upgrade/page_caption_2de08c9.patch) includes its runtime changes and regression file under the saved source's `tests/runtime` layout; reverse-apply check passes against that candidate. It targets `2de08c9`, not this older dirty root checkout.

Verified the active project and disconnected baseline at revision 203 before loading three candidate DATs and reinitializing the extension. Native parameter-page reads resolved `Demo`; the registry, values/modes and other five captured DAT hashes were preserved. The user physically confirmed TD COMP Follow from demo_A to demo_B and back: each main screen showed `Demo`, then restored `EFFECT`, with normal control screens and no FUNC/LEARN/knob action. A hardware right/left arrow-page round trip likewise re-displayed `Demo` after the original three knob mappings recalled, then restored `EFFECT`. Native output observations recorded approximately 2.00–2.30 seconds between those messages, reflecting the deadline and subsequent safe Tick. Exact guarded/mixed-target physical rendering, initial Track-line refresh, new LEARN and unrelated motor behavior were not accepted by these checks. Ordinary connection reconciliation retained the previously recorded stale/Menu limitations.

Removed the temporary outbound observer and restored the complete original software configuration except monotonic revision 221. Original four control definitions/IDs, controller parameters, linked-COMP values/modes, Snapshots, Follow=True, LOCK=False and demo_A context match; no MIDI child remains. Only the three intended runtime DAT hashes differ from the baseline. Refreshed the existing embedded Layout documentation without rebuilding/repositioning the network. The saved-baseline exporter produced a generic tox that reloaded empty/disconnected with no user mappings, Focus/ownership links or Snapshots, embedded helper/docs, `Python=python3` and matching runtime hashes. Scoped native errors are zero.

Saved through live TD and promoted `projects/current/ROTO-CONTROL.toe` and `exports/roto_python.tox`; [project.json](projects/current/project.json) records the base source, patch hash, runtime hashes and artifact hashes. TD's numbered-save convention produced `ROTO-CONTROL.page-caption.20261018.toe`; that suffix is the resulting save counter, not a test date. Recovery copies of the prior canonical artifacts/receipt and original runtime sources are in `projects/archive/page-caption-20261017-recovery`. TD remains open and disconnected. The prior LEARN metadata refactor is still source-only and was not installed by this change. No commit or push.

One-off source extraction, probes and results remain in `/var/folders/5q/krg7wb4d4lsgpmlmgqvywj_w0000gn/T/roto-page-feedback-m_1qjypu`, including `baseline.json`, `candidate-native.json`, `automatic-caption.json`, `physical-follow-acceptance.json`, `physical-page-acceptance.json`, `all-caption-events.json`, `restoration.json`, `generic-export-validation.json` and `save-result.json`. The new caption behavior is documented in [Layouts](docs/functions/layouts.md#main-screen-context). The source patch is retained because the saved runtime baseline is newer than the checkout; the one-off installer/verifiers are not added to the repository.

## Caption PR and documentation correction — 2026-10-17

Created [PR #23](https://github.com/joshuahhn/roto_control/pull/23) from fork main `9f02879` in an isolated worktree, retaining the original dirty checkout. Its source passes 478 tests; the caption runtime is identical to the tested local candidate. The PR contains source/tests/docs and the owner-provided official guidance. Remote canonical artifacts still have their older issue-15-era receipt, so their update would include a separate pre-existing artifact-sync delta. They are excluded from this source-only PR. Local updated artifacts and recovery remain intact; unpublished artifact-preparation branch `feat/td-page-caption` was retained, not rewritten or deleted. The published branch is `feat/td-page-caption-source`.

PR preparation found that the earlier local Layout snapshot had also embedded older ownership/Follow documentation from the dirty checkout. Kept latest-main text, inserted only the caption section, and refreshed the local embedded snapshot/export. Runtime and physical acceptance are unchanged. The refreshed generic export reloaded empty/disconnected, and live TD saved the local project at numbered counter `20261019`; canonical artifact hashes were refreshed in its receipt. That counter is not a date. No other function-document snapshots were replaced.

## LEARN metadata saved-runtime integration — 2026-10-17

After PR creation, the user explicitly selected LEARN metadata integration as the next step. Composed the previously tested scoped refactor over caption PR source `e6a5c2f`, preserving current ownership/transaction code and caption behavior. Updated only protocol, collection_protocol, controls, free_learn and RotoPythonExt DATs. Immutable `LearnParameter` metadata and the pure encoder now serve registered controls, Free LEARN and the legacy Host; formatter introspection and the temporary session-enabled Control are removed. Existing index/hash/Menu signatures, multiple pending offers, matching ACK handling, target writes and routing policy remain on their existing paths.

Final combined source passes `python3 -m unittest discover -q`: 481 tests. A fresh before/after corpus of 163 complete LEARN messages is byte-identical. With the real controller disconnected, native TD captured metadata from its four actual registered controls and four isolated FreeLearner offers reading the same native parameters; all eight packets match before/after. Temporary send callbacks were restored immediately, and the isolated learner had no real Inspector/status or session writes. Native imports share the same `LearnParameter` class, and pending metadata has no connected/session flags. This is native encoding/import evidence, not hardware LEARN/ACK acceptance. No MIDI connection, LEARN operation or parameter/Pulse write was invoked in this integration; prior physical behavior is reused only where packet semantics are unchanged.

Native reload preserved the registry at revision 221, all original four definitions/IDs, controller parameters, linked-COMP values/modes and Snapshots. The eight principal runtime hashes match the combined candidate, with only the intended five changing from the fresh caption baseline; scoped errors are zero. Generic tox reloaded empty/disconnected with no user mappings/Focus/ownership/Snapshots, embedded helper/docs, `Python=python3`, and matching runtime hashes. The existing caption page resolver still reads the native `Demo` page; its nine source regressions pass in the combined suite.

Saved through live TD and promoted local canonical project/tox; receipt now records caption source `e6a5c2f28d3d15a47f6cdbdec8ad38ae295b2b5d` plus [the reproducible LEARN source/test patch](upgrade/learn_metadata_e6a5c2f.patch). The reverse-apply check passes against that candidate. The actual numbered save is `ROTO-CONTROL.page-caption.20261020.toe`, again a counter rather than a test date. Recovery of the preceding caption artifacts/receipt/runtime is in `projects/archive/learn-metadata-20261017-recovery`. TD remains open and disconnected, with no MIDI child. This LEARN integration is local and not part of caption PR #23; no second PR or LEARN integration commit was created.

One-off source extraction, corpus captures and native scripts/results remain in `/var/folders/5q/krg7wb4d4lsgpmlmgqvywj_w0000gn/T/roto-learn-integration-r84fm_j_`, including `baseline.json`, `packets-before.json`, `packets-after.json`, `native-packets-before.json`, `native-packets-after.json`, `candidate-native.json`, `generic-export-validation.json` and `save-result.json`. The retained patch is needed to reproduce the local saved runtime from its published caption baseline without replacing the older dirty root source wholesale.

## Combined caption/LEARN PR — 2026-10-17

The user clarified that caption and LEARN metadata should be delivered in one PR. Added the scoped LEARN source/test delta to the clean `feat/td-page-caption-source` worktree at `e6a5c2f`, committed and pushed `0ed7d975d17a50c193c134cffac97ea63a6ea976`, and updated the existing [PR #23](https://github.com/joshuahhn/roto_control/pull/23) title/body to cover both changes. No second PR was created, and PR #23 remains open against main. GitHub reports mergeable/clean with no configured status checks; the PR is linked to this T3 thread.

Final combined branch discovery passes 481 tests. Its eight principal runtime hashes match the local saved receipt, and the canonical project/tox still match their recorded artifact hashes. Rechecked the retained 163 source packets and eight native TD packets: each before/after pair remains byte-identical. `git diff --check` passes for the complete PR diff. No new native TD, MIDI or hardware acceptance was performed while packaging the PR; the earlier caption physical acceptance and LEARN native encoding/reload evidence retain their stated scopes.

The PR contains source/tests/docs only, including nine caption and three metadata regressions. Older checked-in artifacts and their receipt remain unchanged. The original dirty checkout, current local artifacts, reproducible patches and recovery copies are preserved; only this current overview/handoff were updated locally to reflect the combined PR.

## Generic export sync preparation — 2026-10-17

The user selected generic tox and version receipt synchronization, leaving demo toe synchronization out of scope. Verified the active TD project and read the receipt-designated `/roto_clean_demo/roto_python`: all 19 present runtime/helper DATs match PR source `0ed7d97`, with the four legacy outer-Control/Lister callbacks absent. The currently selected `/roto_control_python/roto_python` is an older separate instance and was observed only.

Loaded the local generic tox in an isolated root fixture. Its 19 runtime/helper DATs match the combined PR; only the embedded README needed refresh. Embedded source Markdown on the detached clone, exported through live TD and reloaded the new tox. All 19 runtime/helper hashes and ten documentation snapshots match `0ed7d975d17a50c193c134cffac97ea63a6ea976`. Reload is empty/disconnected with Follow off, Python=python3, embedded helper, no DAT file dependencies, user mappings, Focus/ownership links or Snapshot records, and zero scoped errors. Quiesced/removed the fixture and verified original controller storage, source DAT hashes and demo parameter values/modes unchanged. No hardware/MIDI or new physical acceptance was invoked.

Promoted the native-saved tox to local `exports/roto_python.tox` with SHA-256 `509911ddcb0d23db9c8db3aa4706140c1475cb64dad4bcd975d659aff125515d`; added `exports/roto_python.json` and an export index. Updated the working-project receipt's generic hash/receipt reference without changing the demo toe bytes. Previous local tox/project receipt are retained under `projects/archive/generic-export-20261017-jh0ke_d6`.

The same generic tox, adjacent receipt and scoped docs are prepared in the existing PR #23 worktree. No commit or push in this step; published PR HEAD remains `0ed7d97` and source-only. The 481-test source result is reused because runtime/scripts/tests did not change. Receipt JSON, artifact SHA-256, all source/documentation hashes and diff checks pass. One-off native script/result, exported tox, prior PR tox and draft updated PR body remain in system temporary `roto-generic-sync-4hp7mefd` and `/tmp/roto-combined-pr-23-body.md`.

## Generic export PR update — 2026-10-17

User requested the next step after the prepared generic export sync. Committed the five scoped export/receipt/index/context/handoff files as `acc7a5cb7fbba234dc2cef80fcf880c19c3d5a99` and pushed to the existing PR #23 branch, without rewriting history or creating another PR. Updated the PR body to include the distributable generic artifact and its broader embedded-runtime sync scope. GitHub readback confirms the new HEAD and open PR; it has not been merged into main.

Rechecked receipt JSON, artifact SHA-256, 19 runtime/helper source hashes and ten Markdown snapshot hashes before commit; staged and complete-PR diff checks pass. Runtime/scripts/tests/demo project and its checked-in receipt were not changed. Reuse the previous 481 source tests and scoped native export/reload evidence; no new TD/MIDI/hardware operation was needed for this publication. The PR worktree is clean, and local dirty-checkout edits/artifacts/recovery remain preserved.

## Track group palette colors — 2026-10-17

Implemented separately on uncommitted `feat/td-track-colors` at
`/Users/huihongnin/.t3/worktrees/roto_control/td-track-colors`, based on `acc7a5c`.
Its HANDOFF records the detailed source/native/hardware scope. The Layout-page
Track color menu and `SetTrackColor` API use the official 83-entry palette;
old records default to 0. Source tests pass 486, scoped Layout tests 26, and
native menu/guard/configured/generic reload checks pass with zero scoped errors.
The user physically confirmed FUNC red/white EFFECT and purple/white COLOR TEST,
then both main-screen names/colors through hardware A/B/A with normal Knob 1–3
screens. Arbitrary RGB and all palette entries were not physically tested.

Only three DATs were installed in `/roto_clean_demo/roto_python`. Removed the
temporary Track/colors and disconnected afterward. Original definitions, four
control IDs, controller parameters, Follow, LOCK and Snapshots are preserved.
Before restoration, demo_A.Amount differed from 0.4 to 0.44924616981016907.
The user confirmed manually changing it during testing. Kept that value/modes
and the matching catalog cache.
Do not claim unchanged target values for the whole physical session.

The open project remains unsaved with the candidate runtime. Saved canonical
toe/tox/receipts, PR #23 and this checkout's runtime sources remain unchanged.
Configured recovery/candidate tox, an empty generic candidate and one-off
evidence are in system temporary `roto-track-color-sgtyqd5s`. The restored
configured candidate is `restored-track-color-candidate.tox`; generic SHA-256 is
`d56ea7cea4b721012c8ef4bcf159c4783661f2d3046b922e1b6b5067c7948cb1`.
No commit, push or PR publication was performed for this feature.

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

## Track color PR and next capability check — 2026-10-17

Published https://github.com/joshuahhn/roto_control/pull/25 against main. Source
commit is `0254000d1f3810fea47713043c8951f6f1d098ee`; export/receipt commit and PR
HEAD is `0ac1adab330f452d238d8159949f19662c9f8fb2`. GitHub readback reports OPEN,
MERGEABLE and no configured status checks. The worktree is clean and the PR is
linked to this thread. PR #23 had already been merged independently; this work
did not merge it. Palette 47's documentation correction is deferred in issue #24.
Source/native/export evidence above remains the final relevant evidence; no new
hardware operation or full project restart was performed during publication.

Began the next meters capability review without changing runtime or hardware.
Official SysEx v1.6 Appendix B.1, PDF pages 34-35, assigns channel-16 CC65-80 to
eight stereo MIX meters; Appendix B.2's PLUGIN table does not list meters.
Section 4.11, PDF page 31, supplies MIX thresholds via 0C 0B. Ableton reference
`_get_meter_changed_listener` sends ordinary CC values and `_setup_meters` sets
MIX thresholds. This documents MIX support, not proof that firmware refuses or
renders those levels in PLUGIN. A concrete TD audio/CHOP use case and mode choice
remain undecided; no meter stream, mode change or queue refactor was added.

## Meter mode and real audio capability acceptance — 2026-10-17

This supersedes the preliminary meter note above. The user supplied
`/roto_clean_demo/demo_au_file_null`, `demo_au_devin_null` and `audioAnalysis` and
authorized exploration. Verified active project `ROTO-CONTROL.track-preview.2.toe`
and controller `/roto_clean_demo/roto_python`; its 19 runtime/helper DAT hashes
match source commit `0254000d1f3810fea47713043c8951f6f1d098ee` throughout. The old
controller was not used. Controller readback returned firmware `3.3.0 eaa37b0`
and SysEx API `1.6`; MIX refresh returned All Tracks / Audio / Level / Mute.

Initial channel-16 CC65/66 patterns produced no bars in either PLUGIN or MIX.
Adding only the reference integration's `0C 0C` meter states, eight values of 1,
also produced no bars in MIX. A complete reference MIX initialization then sent
zero send tracks, current Track metadata and selection, `0C 0B` thresholds
87/113 and the same meter states. The user now observed left/right alternating
104/24 bars in MIX. After switching to PLUGIN, the same bounded CC pattern still
showed only the normal parameter/value. This supports native VU display in MIX
and no native VU display in the tested PLUGIN view on this firmware. The exact
necessary initialization packet within the successful bundle was not isolated;
the earlier failures are not evidence of a hardware or queue defect.

Official Ableton `_send_meters_state` supplies `0C 0C`, absent from the published
SysEx v1.6 command list. Its local source blob
`58a7d08e173959b3394691c0f46f8989bc887502` matched upstream via GitHub API during
this check. Existing external MIDI ownership and JSON queue were reused; no
transport, framing or PLUGIN routing guards were changed.

Real audio probes read existing null CHOP sample arrays at 10 Hz, compute RMS,
and map -60..0 dBFS to meter CC values 0..127. The user confirmed stereo file
bars followed the audio and mono input bars rose/fell together while speaking.
Observed file RMS ranged 0.01486..0.53439 left and 0.01330..0.47477 right; mono
input ranged 0.000620..0.022297. This establishes these supplied CHOP sources
through the temporary reader, not a packaged production meter feature, meter
calibration or opacity/threshold control acceptance. Audio parameters, playback,
gain, outputs and network topology were not changed.

Layer Mix opacity needs a per-layer 0..1 adapter; COMP/base is not assumed to
have a universal opacity parameter. Existing parameter bindings require custom
parameters, so a tool COMP's custom proxy or existing callback route is preferable
to loosening all target guards. For audioAnalysis, trace the selected detector's
pre-comparison level. The observed kick path subtracts `Kickthresh` at `math8`
from `math2`, before `limit4`, `logic1` and `trigger1`; `null_kickSignal` is the
trigger output. MIX color thresholds apply globally, not as independent threshold
markers per meter. Adjusting existing PLUGIN threshold mappings while showing
native MIX bars is not established. A small PLUGIN numeric level/threshold
prototype is an alternative; no such feedback or new MIX input backend was built.

All temporary streams were bounded to 120 seconds, then explicitly stopped and
cleared after observation. A five-second receive trace for version/refresh
readback restored the original trace method. User confirmed PLUGIN and its
normal screen before Disconnect closed/reaped the MIDI child. Connection-time
mapping reconciliation had removed local Button 1 registration; disconnected
restore reinstated all four baseline control IDs. Final native audit confirms
registry equality except monotonic revision 238 to 257, identical controller
parameters and demo_A/B values/modes/expressions, unchanged Snapshots and source
hashes, no pending bytes or probe attributes, and preserved audio nodes. This
restores local definitions, not a readback claim about hardware learned storage.

One-off scripts, recovery tox and detailed results remain only in system temporary
`roto-meter-mode-eprqawbp`. No runtime source edits, new operators, live project
save/export, serial writes, firmware changes, source test run or new PR occurred.
Documentation records the scoped result; embedded snapshots can refresh during
the next authorized save/export. The TD project remains open and disconnected.

## One-knob MIX threshold and motor prototype — 2026-10-17

User selected MIX after clarifying that MIX can control parameters as well as
display meters. No PLUGIN numeric-feedback probe was started. Active project and
controller remained `ROTO-CONTROL.track-preview.2.toe` and
`/roto_clean_demo/roto_python`, with the same 19 source/helper hashes pinned to
`0254000d1f3810fea47713043c8951f6f1d098ee`. Recovery and all one-off scripts/results
are in system temporary `roto-mix-threshold-boeytys3`.

A temporary receiver reused the existing external MIDI process and output
queue, leaving the production PLUGIN parser and readiness guards unchanged.
It first requested MIX refresh and armed only after the actual All Tracks /
Audio / Level / Mute response. The single displayed MIX track was temporarily
named `Kick thresh`, without changing the TD Layout registry. Knob 1 CC12/44
mapped 14-bit input to `audioAnalysis.Kickthresh` over 0..0.6 only while touch52
was on. Release discarded incomplete pairs; a pair older than 250 ms was not
combined. Session, ingress token, routing context, owner, parameter mode,
view and queue guards stopped the probe. Its one-track MIX selection was
consumed locally rather than routed into PLUGIN Track selection.

Only changes to the threshold drove motor output, deferred while touched.
The meter read `audioAnalysis/math2['low']`, the actual pre-comparison low-band
level, and used the same 0..0.6 scale. CC65/66 duplicated that mono level into
the first stereo meter. The single visible lane's yellow/red points followed
the threshold in adjacent 7-bit bins; those color thresholds are global and
this does not establish independent per-lane color thresholds. The control
text showed `T.209 K-`, where K- truthfully indicates disabled Kick detection.
`Kickactive` and `Audioout` remained false; no detector or audio routing was
enabled and actual kick-trigger behavior was not accepted.

User-observed physical results:
- Initial motor moved to about 35%, T.209 K- and simultaneous meter bars passed;
  TD recorded zero business writes before physical touch.
- Turning Knob 1 changed the real threshold from 0.209028 to
  0.26174693279619116, with matching T.262 and continuing meters. There were
  196 changed parameter writes during the user's touch gestures. Original
  demo_A/B values remained unchanged.
- A temporary software edit to 0.450 moved the motor to about 75%, showed
  T.450 K- and kept live meters. Hardware input writes during this hands-off
  motor test were zero.
- Restoring the user's 0.26174693279619116 returned the motor to about 44%,
  T.262 and normal meters. User then confirmed normal PLUGIN screen return.

Streams were bounded, including a fixed maximum overall deadline, and stopped
on PLUGIN entry. The original receive method was restored with no instance
override left behind. Disconnect closed/reaped the MIDI child; pending output
is empty and the probe attribute is removed. Disconnected local-config restore
preserved all four original control IDs and registry definitions except the
monotonic revision 257 to 271. All controller parameters, demo_A/B
values/modes/expressions, Snapshots and source hashes match baseline. The only
audioAnalysis parameter difference is the user's intentional threshold edit;
the agent's temporary 0.450 is not retained. Hardware learned storage was not
read back or re-LEARNed.

Five targeted temporary decoder tests passed for untouched motor messages,
full-range input in either CC order, release and stale-pair handling, wrong
channel/control and invalid data. This is prototype evidence, not a production
MIX regression suite. No production source, new TD operators, canonical toe/tox,
embedded docs, commit or PR was changed. The TD project remains open and
disconnected. A production MIX adapter/configuration remains future work.
Scoped native error checks for the controller, `audioAnalysis/math2` and
`audioAnalysis/math8` returned zero errors/warnings after cleanup.

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

## Native SEL/FUNC MIX mapping design — 2026-10-17

User chose to retain native SEL/FUNC and design each view's mappings first.
The [design proposal](docs/plans/mix-view-mappings.md) replaces the earlier
All Tracks/Level-only delivery assumption. Eight independent MIX slots each
own optional Level/Pan/Send A–L and boolean targets plus a separate meter source.
SEL projects one function across slots; FUNC projects the selected slot's
same target definitions across controls. No duplicate Focus assignments or
parameter-value snapshots are needed. Native function names remain visible.

Read SysEx API v1.6 sections 4.1–4.11 / Appendix B, the official user manual's
printed pages 8–9, and Ableton reference code. Focus sends start after Level/Pan:
the specification says offset CI=08 exposes Send G onward and send-name index 06.
The inspected Ableton formula treats its stored page value differently; actual
second-page readback must be captured before that route is enabled. Reference
Focus metering uses only meter 1 for the selected track; this is a proposed
placement, not new physical acceptance. Focus buttons remain unassigned until
their actual semantics are established. Unsupported channel families/pages
cannot fall back to a Level or PLUGIN target.

Reviewed the clean `td-track-colors` worktree at `0ac1ada` / source `0254000`
for the existing receive/send seams. MIX needs its own business routing before
the PLUGIN Layout/FreeLearner path, including shared General Track messages.
Reuse the existing MIDI owner and parameter conversion, retaining session,
ingress, fresh-touch and frame-tail protections. Global meter thresholds cannot
act as independent per-slot analysis thresholds. The proposal records source,
native and physical verification slices rather than marking them passed.

Only this design document and scoped Context/Handoff notes were added. No
runtime source, TD/controller connection, browser-driven app operation, parameter
write, save/export, source test run, commit or PR is part of this design step.
The interaction diagram uses illustrative routing only and does not contact TD.

## Three-style item/detail contract refinement — 2026-10-17

User described Layer Mix → selected input → Opacity/Brightness/Black Level/Gamma/
Operation/Swap; analysis → selected Low/Mid/High/Kick → its details; audio file/input
→ Gain/Level/Mute. User explicitly confirmed selection can be touch + FUNC and
requested a protocol limited to these three initial styles. The updated
[view proposal](docs/plans/mix-view-mappings.md) and
[contract v1 draft](docs/plans/mix-style-contract.md) use real item/detail labels
and typed targets, with native MIX function addresses kept at the adapter boundary.
No new wire protocol, generic style registry or profile framework is proposed.

Native read-only inspection first confirmed active project
`ROTO-CONTROL.track-preview.2.toe` in the canonical project folder. Low/Mid/High each
expose Threshold/Gain/Add/Smooth/Active and read-only outputs; Kick exposes
Threshold/Active plus Kick detection. Immediate source inspection confirmed file
Volume and no Gain/Mute fields on the current device-input source. Installed
2025.33230 Layer Mix documentation confirms per-layer controls depend on Setup
flags and Operation being Per Layer. No flags or global operations were changed.
The get_help alias `audiodevinCHOP` was not found; the documented class is
`audiodeviceinCHOP`, and actual source parameters were inspected directly.

Audio Level is provisionally treated as read-only RMS, with Gain writable and
Mute retaining Gain. These fields require an explicit destination/stage; metering
the existing nulls does not create gain/mute processing. Analysis meter stage must
be explicit: a public Low output is not automatically the threshold input.
Operation is a full menu and Swap a toggle, with no 16-option truncation claim.

The next physical question is whether native MIX Track Focus can present a Low
item's real four float labels and meter clearly. Fixed Volume/Pan headings and
Focus button behavior are not assumed replaceable. Existing PLUGIN details are
an alternative to evaluate only if native MIX cannot meet the intended flow.
The interactive scenarios describe intent, not a verified firmware UI. This step
changes design/Context/Handoff only; no production source, business parameter,
MIDI connection, save/export, commit or PR changed.

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
